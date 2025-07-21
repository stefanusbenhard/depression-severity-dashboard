# -*- coding: utf-8 -*-
"""
LOSO Results Dashboard (with Feature Meaning)
"""

import pandas as pd
import re
import streamlit as st

# -------------- Mapping dictionaries (no change) --------------
def _landmark_regions():
    mapping = {}
    for i in range(0, 17):
        mapping[f'x{i}'] = 'Jawline'; mapping[f'y{i}'] = 'Jawline'
    for i in range(17, 22):
        mapping[f'x{i}'] = 'Right eyebrow'; mapping[f'y{i}'] = 'Right eyebrow'
    for i in range(22, 27):
        mapping[f'x{i}'] = 'Left eyebrow'; mapping[f'y{i}'] = 'Left eyebrow'
    for i in range(27, 36):
        mapping[f'x{i}'] = 'Nose bridge/tip'; mapping[f'y{i}'] = 'Nose bridge/tip'
    for i in range(36, 42):
        mapping[f'x{i}'] = 'Right eye'; mapping[f'y{i}'] = 'Right eye'
    for i in range(42, 48):
        mapping[f'x{i}'] = 'Left eye'; mapping[f'y{i}'] = 'Left eye'
    for i in range(48, 60):
        mapping[f'x{i}'] = 'Outer lip'; mapping[f'y{i}'] = 'Outer lip'
    for i in range(60, 68):
        mapping[f'x{i}'] = 'Inner lip'; mapping[f'y{i}'] = 'Inner lip'
    return mapping

LANDMARK_REGION_MAP = _landmark_regions()

AU_MEANING_MAP = {
    'AU01': ('Inner brow raiser', 'Terkejut, perhatian'),
    'AU02': ('Outer brow raiser', 'Perhatian, terkejut'),
    'AU04': ('Brow lowerer', 'Cemberut, sedih, khawatir'),
    'AU05': ('Upper lid raiser', 'Terkejut, takut'),
    'AU06': ('Cheek raiser', 'Senyum tulus, bahagia'),
    'AU07': ('Lid tightener', 'Marah, tegang'),
    'AU09': ('Nose wrinkler', 'Jijik'),
    'AU10': ('Upper lip raiser', 'Jijik, meremehkan'),
    'AU12': ('Lip corner puller', 'Senyum, bahagia'),
    'AU15': ('Lip corner depressor', 'Sedih, khawatir'),
    'AU17': ('Chin raiser', 'Ragu, tegang'),
    'AU20': ('Lip stretcher', 'Takut, cemas'),
    'AU23': ('Lip tightener', 'Marah, tegang'),
    'AU26': ('Jaw drop', 'Terkejut, energi rendah'),
    'AU28': ('Lip suck', 'Tidak nyaman'),
    'AU45': ('Blink', 'Lelah, bosan, cemas'),
    # Add more if you use them
}

CUSTOM_CLINICAL_MAP = {
    'blink_rate': ("Frekuensi kedipan", "Kelelahan, bosan, kecemasan (banyak kedipan), perhatian (sedikit kedipan)"),
    'smile_strength': ("Kekuatan senyum", "Afirmasi positif, keterlibatan sosial, anhedonia jika menurun"),
    'frown_intensity': ("Intensitas cemberut", "Afirmasi negatif, distress, kesedihan"),
    'lip_tightness': ("Ketegangan bibir", "Tegang, marah, menahan emosi"),
    'eye_contact': ("Hindari kontak mata", "Menarik diri secara sosial, menghindar, tidak terlibat"),
    'head_smoothness': ("Kelancaran gerakan kepala", "Retardasi psikomotor, perlambatan psikomotor (depresi)"),
    'facial_asymmetry': ("Asimetri wajah", "Kelainan neurologis/psikomotor, penekanan emosi"),
    'emotional_volatility': ("Fluktuasi emosional", "Labilitas mood, ketidakstabilan emosi"),
}

def feature_region_and_meaning(feat):
    base_feat = feat.replace('_c','').replace('_r','').replace('_l','')
    if base_feat in CUSTOM_CLINICAL_MAP:
        return CUSTOM_CLINICAL_MAP[base_feat]
    if base_feat.startswith('x') or base_feat.startswith('y'):
        region = LANDMARK_REGION_MAP.get(base_feat, 'Unknown region')
        meaning = (
            'Gerak kepala, tatapan, ekspresi'
            if region in ['Nose bridge/tip', 'Jawline'] else
            'Gerakan mata, kedipan, tatapan'
            if 'eye' in region else
            'Gerak bibir/mulut'
            if 'lip' in region else
            'Unknown'
        )
        return region, meaning
    m = re.match(r'(AU\d+)', base_feat)
    if m:
        au = m.group(1)
        label, psych = AU_MEANING_MAP.get(au, ('Unknown AU', 'Unknown meaning'))
        return label, psych
    return 'Unknown', 'Unknown'

# -------------- Streamlit UI with Tabs --------------

st.set_page_config(
    page_title="Depression Severity LOSO Dashboard",
    layout="wide",
)

st.title("Depression Severity Prediction – LOSO Dashboard")

FILE_PATH = "dashboard.xlsx"  # Pastikan file ini ada di repo/dir yang sama!

@st.cache_data
def parse_block_excel_file(filepath):
    try:
        df_txt = pd.read_excel(filepath, header=None)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame([])
    lines = df_txt[0].astype(str).tolist()
    results = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r'LOSO fold – hold out (\d+)', line)
        if m:
            subj_id = int(m.group(1))
            selected = []
            true = pred = mae = mse = rmse = None
            if i+1 < len(lines) and 'Selected features:' in lines[i+1]:
                feat_str = lines[i+1].split(':',1)[1].strip()
                try:
                    selected = eval(feat_str)
                except:
                    selected = feat_str
                i += 1
            i += 1
            while i < len(lines):
                l = lines[i].strip()
                if l.startswith('Hold-out'):
                    pass
                elif l.startswith('True:'):
                    parts = re.findall(r"[-+]?\d*\.\d+|\d+", l)
                    if len(parts) >= 2:
                        true = float(parts[0])
                        pred = float(parts[1])
                elif l.startswith('MAE'):
                    mae = float(re.findall(r"[-+]?\d*\.\d+|\d+", l)[0])
                elif l.startswith('MSE'):
                    mse = float(re.findall(r"[-+]?\d*\.\d+|\d+", l)[0])
                elif l.startswith('RMSE'):
                    rmse = float(re.findall(r"[-+]?\d*\.\d+|\d+", l)[0])
                elif l.startswith('LOSO fold'):
                    i -= 1
                    break
                i += 1
            results.append({
                'Subject': subj_id,
                'Selected_Features': selected,
                'True': true,
                'Pred': pred,
                'MAE': mae,
                'MSE': mse,
                'RMSE': rmse,
            })
        i += 1
    return pd.DataFrame(results)

df = parse_block_excel_file(FILE_PATH)
if df.empty:
    st.error("No LOSO blocks found. Check your Excel format.")

if not df.empty:
    tab1, tab2, tab3 = st.tabs([
        "📝 Beranda & Glosarium", 
        "📈 Statistik Dataset", 
        "👤 Analisis Subjek"
    ])

    # Tab 1: Beranda & Glosarium
    with tab1:
        st.header("Tentang Sistem & Glosarium")
        st.markdown("""
        Dashboard ini membantu psikolog memahami hasil prediksi tingkat keparahan depresi menggunakan ciri-ciri wajah.
        
        **Bagaimana cara membacanya?**
        - Sistem memanfaatkan data video wawancara lalu mengekstrak ekspresi wajah dan fitur gerak.
        - Setiap fitur dan hasil prediksi dapat dijelaskan makna psikologisnya.
        - Tujuan: membantu klinisi memahami kapan prediksi dapat dipercaya dan fitur apa saja yang relevan.
        """)
        st.subheader("Glosarium Istilah Penting")
        glos = {
            "Action Unit (AU)": "Kode aktivitas otot wajah (misal: AU06 = senyum, AU04 = cemberut).",
            "Landmark": "Titik pengenalan bentuk wajah (misal: ujung alis, sudut bibir).",
            "MAE": "Rata-rata selisih absolut prediksi dengan nilai sesungguhnya.",
            "PHQ": "Skor depresi hasil kuesioner PHQ.",
            "Fitur Terpilih": "Ciri wajah paling berpengaruh dalam prediksi untuk tiap subjek.",
        }
        for k, v in glos.items():
            st.markdown(f"**{k}:** {v}")
        st.info("Hubungi peneliti jika menemukan istilah yang belum dipahami.")

    # Tab 2: Statistik Dataset (Global)
    with tab2:
        st.header("Statistik Dataset & Fitur Global")
        st.metric("Jumlah Subjek", df['Subject'].nunique())
        st.metric("Rata-rata PHQ", f"{df['True'].mean():.2f}")
        st.metric("Rata-rata MAE", f"{df['MAE'].mean():.2f}")
        st.metric("Rata-rata Prediksi PHQ", f"{df['Pred'].mean():.2f}")
        st.metric("Rata-rata RMSE", f"{df['RMSE'].mean():.2f}")
        st.markdown("---")

        st.subheader("Distribusi MAE dan Prediksi PHQ")
        import matplotlib.pyplot as plt
        import seaborn as sns
        fig, ax = plt.subplots(1,2, figsize=(10,4))
        sns.histplot(df['MAE'], kde=True, ax=ax[0])
        ax[0].set_title('Distribusi MAE')
        ax[0].set_xlabel('MAE')
        sns.scatterplot(x=df['True'], y=df['Pred'], ax=ax[1])
        ax[1].plot([df['True'].min(), df['True'].max()], [df['True'].min(), df['True'].max()], '--', color='gray')
        ax[1].set_xlabel('PHQ Aktual')
        ax[1].set_ylabel('PHQ Prediksi')
        ax[1].set_title('PHQ Aktual vs Prediksi')
        st.pyplot(fig)

        st.markdown("---")
        st.subheader("Top 10 Fitur yang Paling Sering Terpilih Secara Global")
        all_feats = []
        for feats in df['Selected_Features']:
            if isinstance(feats, str):
                feats = eval(feats)
            all_feats.extend(feats)
        from collections import Counter
        top_counts = Counter(all_feats).most_common(10)
        top_tbl = []
        for idx, (feat, count) in enumerate(top_counts, 1):
            region, meaning = feature_region_and_meaning(feat)
            top_tbl.append({
                "Rank": idx,
                "Fitur": feat,
                "Jumlah Terpilih": count,
                "Wilayah/Logika": region,
                "Makna Psikologis": meaning
            })
        st.dataframe(pd.DataFrame(top_tbl))

        st.markdown("---")
        st.subheader("Tabel Data Lengkap")
        st.dataframe(df.sort_values('Subject').reset_index(drop=True))

    # Tab 3: Analisis Subjek (Detail)
    with tab3:
        st.header("Analisis Detail per Subjek")
        subj_list = df['Subject'].sort_values().unique().tolist()
        subj_selected = st.selectbox("Pilih Subject ID", subj_list)
        row = df[df['Subject']==subj_selected].iloc[0]
        st.write(f"### Subjek: {subj_selected}")
        st.write(f"**PHQ Aktual:** {row['True']},  **PHQ Prediksi:** {row['Pred']},  **MAE:** {row['MAE']:.2f}")

        st.write("**Fitur Terpilih (beserta Wilayah & Makna Psikologis):**")
        features = row['Selected_Features']
        if isinstance(features, str):
            features = eval(features)
        options = [5, 10, 15, 20, len(features)]
        labels = [f"Top {n}" for n in options[:-1]] + ["Semua"]
        default_idx = 0
        n_display = st.radio(
            "Berapa banyak fitur yang ingin ditampilkan?",
            options=options, format_func=lambda x: labels[options.index(x)],
            index=default_idx, horizontal=True,
        )
        show_feats = features[:n_display]
        for idx, f in enumerate(show_feats, 1):
            region, meaning = feature_region_and_meaning(f)
            st.markdown(
                f"**{idx}.** `{f}`  \n"
                f"&emsp;• **Wilayah/Logika:** {region}  \n"
                f"&emsp;• **Makna Psikologis:** *{meaning}*"
            )
        if n_display < len(features):
            st.caption(f"Menampilkan top {n_display} dari total {len(features)} fitur. Ubah opsi untuk lihat semua.")
        if abs(row['True']-row['Pred'])>5:
            st.warning(f"Error prediksi tinggi! (>|5|)")

        # Legend
        with st.expander("Legenda Action Unit & Landmark"):
            st.markdown("#### Action Unit (FACS) Umum")
            au_tbl = pd.DataFrame([
                {'AU': k, 'Wilayah/Otot': v[0], 'Makna Psikologis': v[1]}
                for k,v in AU_MEANING_MAP.items()
            ])
            st.dataframe(au_tbl)
            st.markdown("#### Landmark Wajah (Dlib 68)")
            st.write("""
- **x0–x16 / y0–y16:** Jawline (rahang)
- **x17–x21 / y17–y21:** Right eyebrow (alis kanan)
- **x22–x26 / y22–y26:** Left eyebrow (alis kiri)
- **x27–x35 / y27–y35:** Nose bridge & tip (hidung)
- **x36–x41 / y36–y41:** Right eye (mata kanan)
- **x42–x47 / y42–y47:** Left eye (mata kiri)
- **x48–x59 / y48–y59:** Outer lip (bibir luar)
- **x60–x67 / y60–y67:** Inner lip (bibir dalam)
            """)
            st.markdown("#### Fitur Klinis Kustom")
            custom_tbl = pd.DataFrame([
                {'Fitur': k, 'Wilayah/Logika': v[0], 'Makna Psikologis': v[1]}
                for k,v in CUSTOM_CLINICAL_MAP.items()
            ])
            st.dataframe(custom_tbl)
