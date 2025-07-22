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

st.title("Dashboard Sistem Prediksi Tingkat Keparahan Depresi")
st.subheader("dengan Patient Health Questionnaire 8 (PHQ-8)")
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
        # Tab 1: Beranda & Glosarium
    
    with tab1:
        st.markdown("""
        <div>
            <b>🔎 Konteks Studi & Peran Psikolog</b><br><br>
            <ul style='margin-left:-20px'>
                <li>Anda diminta membantu <b>menilai dan memahami hasil analisis ekspresi wajah</b> dari rekaman wawancara pasien depresi.</li>
                <li>Semua data yang Anda lihat adalah hasil ekstraksi otomatis dari video, lalu diproses agar mudah dianalisis oleh psikolog.</li>
                <li>Task Psikolog: <b>Membaca hasil prediksi sistem</b> dan melihat fitur wajah yang <b>paling berperan</b> dalam hasil tersebut.</li>
                <li>Dashboard ini bukan alat diagnosis, tapi sebagai <u>bahan pertimbangan tambahan</u> untuk interpretasi klinis.</li>
                <li>Jika Anda belum pernah menggunakan sistem serupa, cukup ikuti <b>langkah-langkah di bawah ini</b> dan baca glosarium istilah.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Checklist/Kanban for process
        st.markdown("""
        ### Cara Membaca Dashboard (Langkah-langkah Mudah)
        1. **Buka tab Statistik Dataset** (📈):  
           ➔ Untuk melihat gambaran umum hasil prediksi sistem dan pola yang muncul.
        2. **Buka tab Analisis Subjek** (👤):  
           ➔ Untuk menelusuri hasil detail per pasien, termasuk fitur wajah yang paling dominan.
        3. **Butuh penjelasan istilah?**  
           ➔ Buka bagian Glosarium di bawah ini.
        """)

        with st.expander("🔍 Glosarium & Penjelasan Istilah (klik untuk lihat penjelasan)", expanded=True):
            glossary_points = [
                ("**Action Unit (AU)**", "Kode aktivitas otot wajah (contoh: AU06 = senyum, AU04 = cemberut)."),
                ("**Landmark**", "Titik kunci di wajah untuk analisis bentuk/gerak (misal: ujung alis, sudut bibir)."),
                ("**MAE**", "Rata-rata selisih absolut antara prediksi sistem dan skor PHQ sebenarnya (makin kecil = makin akurat)."),
                ("**PHQ**", "Skor depresi dari kuesioner PHQ-8, standar klinis."),
                ("**Fitur Terpilih**", "Fitur wajah yang paling mempengaruhi hasil prediksi pada pasien."),
            ]
            for word, desc in glossary_points:
                st.markdown(f"- {word}: {desc}")
            st.info("Jika menemukan istilah baru atau membingungkan, silakan cek di sini atau hubungi peneliti.")

        st.markdown("""
        ---
        **FAQ (Sering Ditanyakan):**
        - <b>Apa manfaat dashboard ini?</b>  
        → Membantu Anda menambah wawasan dalam membaca ekspresi wajah pasien secara kuantitatif, bukan menggantikan intuisi klinis.
        - <b>Apakah dashboard ini hanya untuk diagnosis?</b>  
        → Tidak. Hasil di sini untuk <u>melengkapi</u> penilaian profesional Anda.
        - <b>Saya belum pernah pakai sistem serupa, apakah aman?</b>  
        → Iya. Cukup ikuti instruksi dan gunakan Glosarium sebagai panduan istilah.

        <br>
        <b>Butuh bantuan lebih lanjut? Kontak peneliti:</b>  
        <a href="mailto:stefanus@example.com">stefanus.benhard@binus.ac.id</a>
        """, unsafe_allow_html=True)



    # Tab 2: Statistik Dataset (Global)
with tab2:
    st.header("Gambaran Umum Hasil Sistem (Statistik Global)")

    st.markdown("""
    <div>
        <b>Apa yang Anda lihat di sini?</b><br>
        Statistik ini merangkum performa sistem dalam memprediksi tingkat keparahan depresi (PHQ-8) di seluruh subjek. 
        <ul>
            <li><b>Semua data di bawah</b> adalah hasil <u>analisis otomatis ekspresi wajah</u> selama wawancara.</li>
            <li>Angka-angka disini <b>membantu Anda menilai seberapa konsisten dan akurat sistem</b>.</li>
            <li><b>Bukan untuk alat diagnosis</b> namun sebagai insight tambahan selama proses wawancara.</li>
                <li><b>PHQ-8</b> adalah kuesioner depresi standar klinis, dengan skor antara <b>0 (tidak depresi)</b> sampai <b>24 (depresi berat)</b>.</li>
        <li><b>MAE (Mean Absolute Error)</b> = rata-rata selisih prediksi sistem dengan skor PHQ-8 asli pasien.<br>
        <li>
        Contoh: MAE = 3 artinya, rata-rata sistem salah prediksi sekitar 3 poin PHQ-8 per pasien.
        </li>
        <li>Semakin kecil MAE, semakin akurat sistem dalam memperkirakan tingkat depresi pasien.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    colA, colB, colC, colD, colE = st.columns(5)
    colA.metric("Jumlah Subjek", df['Subject'].nunique())
    colB.metric("Rata-rata PHQ", f"{df['True'].mean():.2f}")
    colC.metric("Rata-rata MAE", f"{df['MAE'].mean():.2f}")
    colD.metric("Rata-rata Prediksi PHQ", f"{df['Pred'].mean():.2f}")
    colE.metric("Rata-rata RMSE", f"{df['RMSE'].mean():.2f}")

    st.markdown("---")
    st.subheader("Visualisasi Hasil Prediksi Sistem")

    st.markdown("""
    <ul>
        <li><b>Grafik kiri</b> memperlihatkan distribusi error prediksi sistem (MAE).</li>
        <li><b>Grafik kanan</b> membandingkan skor PHQ hasil prediksi sistem dengan nilai aktual tiap subjek.</li>
        <li>Semakin dekat titik-titik pada garis abu-abu, semakin baik prediksinya.</li>
    </ul>
    """, unsafe_allow_html=True)

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
    st.subheader("10 Fitur Wajah Paling Sering Berpengaruh")
    st.markdown("""
    <ul>
        <li>Daftar berikut menunjukkan fitur wajah (atau gerak) yang <b>paling sering terlibat</b> dalam prediksi sistem di seluruh pasien.</li>
        <li>Makna psikologis setiap fitur dijelaskan di kolom kanan (tidak perlu paham istilah teknis!).</li>
        <li>Data ini berguna untuk mencari <b>pola ekspresi wajah</b> yang mungkin relevan secara klinis.</li>
    </ul>
    """, unsafe_allow_html=True)
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
            "Wilayah Wajah": region,
            "Makna Psikologis": meaning
        })
    st.dataframe(pd.DataFrame(top_tbl))

    st.markdown("#### Ilustrasi Titik Landmark & Action Unit pada Wajah")
    colA, colB = st.columns(2)
    with colA:
        st.image("landmarks.png", caption="Nomor Titik Landmark Wajah (Dlib 68-point)", use_column_width=True)
        st.caption("Setiap titik bernomor mewakili bagian wajah untuk analisis ekspresi & gerak. Contoh: x36 = sudut luar mata kanan.")
    with colB:
        st.image("action_units.png", caption="Lokasi Action Unit (AU) FACS pada Wajah", use_column_width=True)
        st.caption("Action Unit (AU) menunjukkan aktivitas otot tertentu. Contoh: AU06 = Senyum, AU04 = Cemberut.")
    st.info(
        "Keterangan: Titik landmark dan Action Units ini digunakan sistem untuk mendeteksi pola ekspresi yang relevan dalam prediksi skor PHQ-8 secara otomatis."
    )

    df_simplified = df.drop(columns=['MSE', 'RMSE'], errors='ignore')
    # Mapping for pretty clinician-friendly names
    nice_columns = {
        "Subject": "ID Subjek",
        "Selected_Features": "Fitur",
        "True": "PHQ Aktual",
        "Pred": "PHQ Prediksi AI",
        "MAE": "MAE (Error Rata-rata)"
    }

    # Use this before st.dataframe in Tab 2
    df_display = df_simplified.rename(columns=nice_columns)
    st.subheader("Tabel Data Lengkap (untuk telusuri semua hasil per subjek)")
    st.caption("Gunakan tabel di bawah ini untuk mencari, mengurutkan, atau menelusuri semua hasil prediksi per pasien. Untuk analisis masing-masing subjek klik tab 👤 Analisis Subjek")
    st.dataframe(df_display.sort_values('ID Subjek').reset_index(drop=True))



    # Tab 3: Analisis Subjek (Detail)
    with tab3:
        st.header("Analisis Detail per Subjek (Pasien)")
        st.markdown("""
        <b>Panduan Membaca Halaman Ini:</b>
        <ol>
            <li>Pilih ID subjek (pasien)</li>
            <li>Lihat prediksi skor depresi oleh sistem AI (PHQ-8) dan bandingkan dengan nilai aktual.</li>
            <li>Cermati daftar fitur wajah yang <u>paling berpengaruh</u> dalam hasil prediksi untuk subjek ini.</li>
            <li>Gunakan tabel & gambar di bawah untuk memahami wilayah/otot wajah yang relevan.</li>
            <li>Jika ada error prediksi tinggi, gunakan info fitur ini sebagai insight tambahan, bukan keputusan diagnosis akhir.</li>
        </ol>
        """, unsafe_allow_html=True)

        subj_list = df['Subject'].sort_values().unique().tolist()
        subj_selected = st.selectbox("Pilih ID Subjek (Pasien)", subj_list)
        row = df[df['Subject']==subj_selected].iloc[0]

        # Rename columns for consistency with Tab 2
        col_names = {
            "Subject": "ID Subjek",
            "True": "PHQ Aktual",
            "Pred": "PHQ Prediksi",
            "MAE": "MAE (Error Rata-rata)",
            "Selected_Features": "Fitur Terpilih",
        }

        st.markdown(f"### Subjek: **{row['Subject']}**")
        st.write(
            f"<ul>"
            f"<li><b>Nilai PHQ Aktual:</b> {row['True']}</li>"
            f"<li><b>Nilai PHQ Prediksi AI:</b> {row['Pred']}</li>"
            f"<li><b>MAE (Error Rata-rata):</b> {row['MAE']:.2f}</li>"
            f"</ul>",
            unsafe_allow_html=True
        )

        st.info("MAE artinya rata-rata perbedaan skor PHQ-8 hasil prediksi sistem dibandingkan dengan skor asli pasien (range PHQ-8: 0=tidak depresi s.d. 24=depresi berat).")

        st.markdown("#### Fitur Wajah Terpilih (Paling Berpengaruh untuk Subjek Ini)")
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
                f"**{idx}.** <code>{f}</code><br>"
                f"&emsp;• <b>Wilayah/Logika:</b> {region}<br>"
                f"&emsp;• <b>Makna Psikologis:</b> <i>{meaning}</i>",
                unsafe_allow_html=True
            )
        if n_display < len(features):
            st.caption(f"Menampilkan top {n_display} dari total {len(features)} fitur. Ubah opsi untuk lihat semua.")

        if abs(row['True']-row['Pred']) > 5:
            st.warning("⚠️ Error prediksi cukup tinggi (>5 poin PHQ). Silakan gunakan informasi fitur sebagai referensi tambahan.")

        # Add facial images for context
        st.markdown("#### Ilustrasi Titik Landmark & Action Unit pada Wajah")
        colA, colB = st.columns(2)
        with colA:
            st.image("landmarks.png", caption="Nomor Titik Landmark Wajah (Dlib 68-point)", use_column_width=True)
            st.caption("Setiap titik bernomor mewakili bagian wajah untuk analisis ekspresi & gerak. Contoh: x36 = sudut luar mata kanan.")
        with colB:
            st.image("action_units.png", caption="Lokasi Action Unit (AU) FACS pada Wajah", use_column_width=True)
            st.caption("Action Unit (AU) menunjukkan aktivitas otot tertentu. Contoh: AU06 = Senyum, AU04 = Cemberut.")
        st.info("Gambar di atas membantu Anda memahami posisi setiap fitur wajah yang digunakan dalam analisis otomatis oleh sistem.")

        # Keep the legend/expander for completeness (optional, but can be simplified if pictures already there)
        with st.expander("Legenda Action Unit & Landmark (Daftar Lengkap)"):
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

