# -*- coding: utf-8 -*-
"""
LOSO Results Dashboard (with Feature Meaning)
"""

import pandas as pd
import re
import streamlit as st

# --------- AU and Landmark Dictionaries for Meaningful Annotation ----------
# 68-point Dlib face landmark indices (full for x and y coordinates)
def _landmark_regions():
    mapping = {}
    # Jawline
    for i in range(0, 17):
        mapping[f'x{i}'] = 'Jawline'
        mapping[f'y{i}'] = 'Jawline'
    # Eyebrows
    for i in range(17, 22):
        mapping[f'x{i}'] = 'Right eyebrow'
        mapping[f'y{i}'] = 'Right eyebrow'
    for i in range(22, 27):
        mapping[f'x{i}'] = 'Left eyebrow'
        mapping[f'y{i}'] = 'Left eyebrow'
    # Nose
    for i in range(27, 36):
        mapping[f'x{i}'] = 'Nose bridge/tip'
        mapping[f'y{i}'] = 'Nose bridge/tip'
    # Eyes
    for i in range(36, 42):
        mapping[f'x{i}'] = 'Right eye'
        mapping[f'y{i}'] = 'Right eye'
    for i in range(42, 48):
        mapping[f'x{i}'] = 'Left eye'
        mapping[f'y{i}'] = 'Left eye'
    # Mouth/Chin
    for i in range(48, 60):
        mapping[f'x{i}'] = 'Outer lip'
        mapping[f'y{i}'] = 'Outer lip'
    for i in range(60, 68):
        mapping[f'x{i}'] = 'Inner lip'
        mapping[f'y{i}'] = 'Inner lip'
    return mapping

LANDMARK_REGION_MAP = _landmark_regions()

AU_MEANING_MAP = {
    'AU01': ('Inner brow raiser', 'Surprise, attentiveness'),
    'AU02': ('Outer brow raiser', 'Attentiveness, surprise'),
    'AU04': ('Brow lowerer', 'Frown, sadness, concern'),
    'AU05': ('Upper lid raiser', 'Surprise, fear'),
    'AU06': ('Cheek raiser', 'Genuine smile, happiness'),
    'AU07': ('Lid tightener', 'Anger, tension'),
    'AU09': ('Nose wrinkler', 'Disgust'),
    'AU10': ('Upper lip raiser', 'Disgust, contempt'),
    'AU12': ('Lip corner puller', 'Smile, happiness'),
    'AU15': ('Lip corner depressor', 'Sadness, concern'),
    'AU17': ('Chin raiser', 'Doubt, tension'),
    'AU20': ('Lip stretcher', 'Fear, anxiety'),
    'AU23': ('Lip tightener', 'Anger, tension'),
    'AU26': ('Jaw drop', 'Surprise, low energy'),
    'AU28': ('Lip suck', 'Uncertainty, discomfort'),
    'AU45': ('Blink', 'Fatigue, boredom, anxiety'),
    # Add more if you use them
}

# --- Custom engineered/clinical features (YOUR NOVEL FEATURES) ---
CUSTOM_CLINICAL_MAP = {
    'blink_rate': ("Blink rate", "Fatigue, boredom, anxiety, disengagement (high blink), engagement (low blink)"),
    'smile_strength': ("Smile strength", "Positive affect, social engagement, anhedonia if reduced"),
    'frown_intensity': ("Frown intensity", "Negative affect, distress, sadness"),
    'lip_tightness': ("Lip tightness", "Tension, anger, suppression of affect"),
    'eye_contact': ("Eye contact avoidance", "Social withdrawal, avoidance, disengagement"),
    'head_smoothness': ("Head movement smoothness", "Psychomotor retardation, psychomotor slowing (depression)"),
    'facial_asymmetry': ("Facial asymmetry", "Neurological or psychomotor abnormality, emotional suppression"),
    'emotional_volatility': ("Emotional volatility (AU fluctuation)", "Mood lability, emotional instability, affective reactivity"),
}


def feature_region_and_meaning(feat):
    base_feat = feat.replace('_c','').replace('_r','').replace('_l','')
    # 1. Check for custom/engineered features
    if base_feat in CUSTOM_CLINICAL_MAP:
        return CUSTOM_CLINICAL_MAP[base_feat]
    # 2. Landmark
    if base_feat.startswith('x') or base_feat.startswith('y'):
        region = LANDMARK_REGION_MAP.get(base_feat, 'Unknown region')
        meaning = (
            'Head movement, gaze, expression'
            if region in ['Nose bridge/tip', 'Jawline'] else
            'Eye movement, blink, gaze'
            if 'eye' in region else
            'Lip/mouth movement'
            if 'lip' in region else
            'Unknown'
        )
        return region, meaning
    # 3. AU
    m = re.match(r'(AU\d+)', base_feat)
    if m:
        au = m.group(1)
        label, psych = AU_MEANING_MAP.get(au, ('Unknown AU', 'Unknown meaning'))
        return label, psych
    # 4. Unknown
    return 'Unknown', 'Unknown'


# -------------- Streamlit UI --------------

st.set_page_config(
    page_title="Depression Severity LOSO Dashboard",
    layout="wide",
)
st.title("Depression Severity Prediction – LOSO Dashboard")

uploaded_file = st.file_uploader(
    "Upload the LOSO results Excel (block style, 1 column):",
    type=["xlsx", "xls"]
)

@st.cache_data
def parse_block_excel(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame([])
    df_txt = pd.read_excel(uploaded_file, header=None)
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
            # Selected features next
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

# --- LOAD & PARSE ---
if uploaded_file:
    df = parse_block_excel(uploaded_file)
    if df.empty:
        st.error("No LOSO blocks found. Check your Excel format.")
else:
    df = pd.DataFrame([])

# --- DASHBOARD ---
if not df.empty:
    st.success(f"Parsed {len(df)} LOSO folds.")
    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("Overall Statistics")
        st.metric("Mean MAE", f"{df['MAE'].mean():.2f}")
        st.metric("Median MAE", f"{df['MAE'].median():.2f}")
        st.metric("Best (lowest) MAE", f"{df['MAE'].min():.2f}")
        st.metric("Worst (highest) MAE", f"{df['MAE'].max():.2f}")
        st.metric("Mean RMSE", f"{df['RMSE'].mean():.2f}")
        st.metric("Mean True PHQ", f"{df['True'].mean():.2f}")
        st.metric("Mean Predicted PHQ", f"{df['Pred'].mean():.2f}")

        st.markdown("---")
        st.subheader("Top (Lowest MAE)")
        st.dataframe(df.nsmallest(189, 'MAE')[['Subject','True','Pred','MAE']].reset_index(drop=True))
        st.subheader("Top (Highest MAE)")
        st.dataframe(df.nlargest(189, 'MAE')[['Subject','True','Pred','MAE']].reset_index(drop=True))

    with col2:
        st.subheader("Distribution Plots")
        import matplotlib.pyplot as plt
        import seaborn as sns
        fig, ax = plt.subplots(1,2, figsize=(10,4))
        sns.histplot(df['MAE'], kde=True, ax=ax[0])
        ax[0].set_title('MAE Distribution')
        ax[0].set_xlabel('MAE')
        sns.scatterplot(x=df['True'], y=df['Pred'], ax=ax[1])
        ax[1].plot([df['True'].min(), df['True'].max()], [df['True'].min(), df['True'].max()], '--', color='gray')
        ax[1].set_xlabel('True PHQ')
        ax[1].set_ylabel('Predicted PHQ')
        ax[1].set_title('True vs Predicted PHQ')
        st.pyplot(fig)

        st.markdown("---")
        st.subheader("Full Data Table (searchable)")
        st.dataframe(df.sort_values('Subject').reset_index(drop=True))

        # --- GLOBAL TOP 10 FEATURES ---
        st.subheader("Top Globally Most Selected Features")

        # Flatten all selected features
        all_feats = []
        for feats in df['Selected_Features']:
            if isinstance(feats, str):
                feats = eval(feats)
            all_feats.extend(feats)

        from collections import Counter
        top_counts = Counter(all_feats).most_common()

        # Prepare pretty table with region/meaning
        top_tbl = []
        for idx, (feat, count) in enumerate(top_counts, 1):
            region, meaning = feature_region_and_meaning(feat)
            top_tbl.append({
                "Rank": idx,
                "Feature": feat,
                "Times Selected": count,
                "Region/Logic": region,
                "Psychological Meaning": meaning
            })

        st.dataframe(pd.DataFrame(top_tbl))


    st.markdown("---")
    # --- DETAILED INSIGHT DROPDOWN ---
    st.subheader(":mag_right: Detailed View (by Subject)")
    subj_list = df['Subject'].sort_values().unique().tolist()
    subj_selected = st.selectbox("Select Subject ID", subj_list)
    row = df[df['Subject']==subj_selected].iloc[0]
    st.write(f"### Subject: {subj_selected}")
    st.write(f"**True PHQ:** {row['True']},  **Predicted PHQ:** {row['Pred']},  **MAE:** {row['MAE']:.2f}")
    # ---- Feature annotation ----
        # ---- Feature annotation (original order, interactive) ----
    st.write("**Selected Features (with Region & Psychological Meaning):**")
    features = row['Selected_Features']
    if isinstance(features, str):
        features = eval(features)

    # Count options
    options = [5, 10, 15, 20, len(features)]
    labels = [f"Top {n}" for n in options[:-1]] + ["All"]
    default_idx = 0

    n_display = st.radio(
        "How many features to display?",
        options=options, format_func=lambda x: labels[options.index(x)],
        index=default_idx, horizontal=True,
    )

    show_feats = features[:n_display]
    for idx, f in enumerate(show_feats, 1):
        region, meaning = feature_region_and_meaning(f)
        st.markdown(
            f"**{idx}.** `{f}`  \n"
            f"&emsp;• **Region/Logic:** {region}  \n"
            f"&emsp;• **Psychological Meaning:** *{meaning}*"
        )

    if n_display < len(features):
        st.caption(f"Showing top {n_display} of {len(features)} features. Use selector above to see more.")


    # Quick Error Analysis
    if abs(row['True']-row['Pred'])>5:
        st.warning(f"High prediction error detected! (>|5|)")

    # --- Expandable: Show full AU and Landmark cheat sheet for clinicians
    with st.expander("Legend: Action Units & Landmark Meanings"):
        st.markdown("#### Common Action Units (FACS)")
        au_tbl = pd.DataFrame([
            {'AU': k, 'Region/Muscle': v[0], 'Psychological Meaning': v[1]}
            for k,v in AU_MEANING_MAP.items()
        ])
        st.dataframe(au_tbl)
        st.markdown("#### Facial Landmarks (Dlib 68)")
        st.write("""
- **x0–x16 / y0–y16:** Jawline
- **x17–x21 / y17–y21:** Right eyebrow
- **x22–x26 / y22–y26:** Left eyebrow
- **x27–x35 / y27–y35:** Nose bridge & tip
- **x36–x41 / y36–y41:** Right eye
- **x42–x47 / y42–y47:** Left eye
- **x48–x59 / y48–y59:** Outer lip
- **x60–x67 / y60–y67:** Inner lip
        """)
        st.markdown("#### Custom Clinical Features (Engineered)")
        custom_tbl = pd.DataFrame([
            {'Feature': k, 'Region/Logic': v[0], 'Psychological Meaning': v[1]}
            for k,v in CUSTOM_CLINICAL_MAP.items()
        ])
        st.dataframe(custom_tbl)

else:
    st.info("Upload a file to begin analysis.")
