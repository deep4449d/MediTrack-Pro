import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os

st.set_page_config(page_title="MediTrack Pro", page_icon="🏥", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #060d1a; }
[data-testid="stHeader"] { background-color: #060d1a; }
h1,h2,h3,h4 { color: #00c8ff !important; }
[data-testid="metric-container"] {
    background: #0c1628;
    border: 1px solid #1a2e4a;
    border-radius: 10px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

FILE = "inventory.csv"

def get_default():
    return pd.DataFrame({
        'Medicine'     : ['Paracetamol','Insulin','Amoxicillin','Aspirin','Gloves (Box)','Vitamin C','Metformin','Surgical Mask'],
        'Category'     : ['Painkiller','Diabetes','Antibiotic','Cardiac','Equipment','Vitamin','Diabetes','Surgical'],
        'Current_Stock': [150,18,80,10,30,200,5,500],
        'Minimum_Stock': [50,20,30,50,20,40,30,100],
        'Unit_Price'   : [2,150,45,5,350,8,12,3],
        'Expiry_Date'  : ['2026-08-15','2026-05-20','2027-01-10','2026-03-15',
                          '2027-06-01','2026-12-01','2026-07-20','2027-03-01']
    })

def load():
    df = pd.read_csv(FILE) if os.path.exists(FILE) else get_default()
    df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'], errors='coerce')
    df['Days_Left']   = (df['Expiry_Date'] - pd.Timestamp.now()).dt.days
    df['Status']      = df.apply(lambda r: '🚨 Critical' if r['Current_Stock'] <= r['Minimum_Stock']*0.5
                                 else ('⚠️ Low' if r['Current_Stock'] <= r['Minimum_Stock'] else '✅ OK'), axis=1)
    df['Total_Value'] = df['Current_Stock'] * df['Unit_Price']
    return df

def save(df):
    out = df[['Medicine','Category','Current_Stock','Minimum_Stock','Unit_Price','Expiry_Date']].copy()
    out['Expiry_Date'] = pd.to_datetime(out['Expiry_Date']).dt.strftime('%Y-%m-%d')
    out.to_csv(FILE, index=False)

df = load()
CATS = ['Painkiller','Antibiotic','Diabetes','Cardiac','Equipment','Vitamin','Surgical','Other']

st.markdown("# 🏥 MediTrack Pro")
st.caption("Because Every Medicine Counts.")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", "📋 Inventory", "➕ Add Medicine", "✏️ Update Medicine", "📁 Upload CSV"
])

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💊 Total Medicines", len(df))
    c2.metric("🚨 Critical",        len(df[df['Status']=='🚨 Critical']))
    c3.metric("⏳ Expiring in 30d", len(df[(df['Days_Left']>=0)&(df['Days_Left']<=30)]))
    c4.metric("💰 Total Value",     f"₹{df['Total_Value'].sum():,.0f}")

    st.markdown("---")
    cat_grp = df.groupby('Category')['Current_Stock'].sum().reset_index()

    l,r = st.columns(2)
    with l:
        st.markdown("#### Stock by Category")
        fig = px.bar(cat_grp, x='Category', y='Current_Stock', color='Category',
                     template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_layout(plot_bgcolor='#0c1628', paper_bgcolor='#0c1628',
                          showlegend=False, height=280, margin=dict(l=5,r=5,t=5,b=5))
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.markdown("#### Category Split")
        fig2 = px.pie(cat_grp, names='Category', values='Current_Stock', hole=0.45,
                      template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Bold)
        fig2.update_layout(plot_bgcolor='#0c1628', paper_bgcolor='#0c1628',
                           height=280, margin=dict(l=5,r=5,t=5,b=5))
        st.plotly_chart(fig2, use_container_width=True)

    l2,r2 = st.columns(2)
    with l2:
        st.markdown("#### Current vs Minimum Stock")
        low6 = df.sort_values('Current_Stock').head(6)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Current', x=low6['Medicine'], y=low6['Current_Stock'], marker_color='#00c8ff'))
        fig3.add_trace(go.Bar(name='Minimum', x=low6['Medicine'], y=low6['Minimum_Stock'], marker_color='#ff3d5a'))
        fig3.update_layout(barmode='group', template='plotly_dark',
                           plot_bgcolor='#0c1628', paper_bgcolor='#0c1628',
                           height=280, margin=dict(l=5,r=5,t=5,b=5))
        st.plotly_chart(fig3, use_container_width=True)

    with r2:
        st.markdown("#### Top 6 by Value")
        top6 = df.sort_values('Total_Value', ascending=True).tail(6)
        fig4 = px.bar(top6, x='Total_Value', y='Medicine', orientation='h',
                      color='Total_Value', color_continuous_scale='Blues', template='plotly_dark')
        fig4.update_layout(plot_bgcolor='#0c1628', paper_bgcolor='#0c1628',
                           height=280, margin=dict(l=5,r=5,t=5,b=5), coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔔 Alerts")
    crits = df[df['Status']=='🚨 Critical']
    lows  = df[df['Status']=='⚠️ Low']
    exp   = df[(df['Days_Left']>=0)&(df['Days_Left']<=30)]

    if len(crits)==0 and len(lows)==0 and len(exp)==0:
        st.success("✅ All stock levels are fine. No alerts.")
    for _,row in crits.iterrows():
        st.error(f"🚨 **{row['Medicine']}** — Only {row['Current_Stock']} units left | Min required: {row['Minimum_Stock']} | CRITICAL")
    for _,row in lows.iterrows():
        st.warning(f"⚠️ **{row['Medicine']}** — {row['Current_Stock']} units | Min required: {row['Minimum_Stock']} | LOW STOCK")
    for _,row in exp.iterrows():
        st.warning(f"⏳ **{row['Medicine']}** — Expires in {int(row['Days_Left'])} days ({row['Expiry_Date'].strftime('%d %b %Y')})")

# ── INVENTORY TABLE ───────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### 📋 Full Inventory")
    s1,s2,s3 = st.columns(3)
    search = s1.text_input("🔍 Search", placeholder="Medicine name...")
    f_cat  = s2.selectbox("Category", ["All"]+sorted(df['Category'].unique().tolist()))
    f_stat = s3.selectbox("Status",   ["All","✅ OK","⚠️ Low","🚨 Critical"])

    res = df.copy()
    if search:       res = res[res['Medicine'].str.contains(search, case=False, na=False)]
    if f_cat  != "All": res = res[res['Category']==f_cat]
    if f_stat != "All": res = res[res['Status']==f_stat]

    show = res[['Medicine','Category','Current_Stock','Minimum_Stock',
                'Unit_Price','Expiry_Date','Days_Left','Status','Total_Value']].copy()
    show['Expiry_Date'] = res['Expiry_Date'].dt.strftime('%d %b %Y').values
    show['Unit_Price']  = res['Unit_Price'].apply(lambda x: f"₹{x}").values
    show['Total_Value'] = res['Total_Value'].apply(lambda x: f"₹{x:,.0f}").values
    show['Days_Left']   = res['Days_Left'].apply(lambda x: f"{int(x)}d").values

    st.dataframe(show, use_container_width=True, height=400)
    st.caption(f"{len(res)} of {len(df)} records")

    exp_df = df[['Medicine','Category','Current_Stock','Minimum_Stock','Unit_Price','Expiry_Date']].copy()
    exp_df['Expiry_Date'] = exp_df['Expiry_Date'].dt.strftime('%Y-%m-%d')
    st.download_button("⬇️ Download CSV", exp_df.to_csv(index=False), "inventory.csv", "text/csv")

# ── ADD NEW MEDICINE ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### ➕ Add New Medicine")
    st.info("Only use this to add a medicine that is not already in the inventory.")

    with st.form("add_form", clear_on_submit=True):
        a1,a2 = st.columns(2)
        nm  = a1.text_input("Medicine Name *")
        cat = a2.selectbox("Category *", ['Select...']+CATS)
        b1,b2,b3 = st.columns(3)
        stk = b1.number_input("Current Stock *", min_value=0, step=1)
        mn  = b2.number_input("Minimum Stock *", min_value=1, step=1, value=10)
        prc = b3.number_input("Unit Price ₹ *",  min_value=0.0, step=0.5)
        exp = st.date_input("Expiry Date *", min_value=date.today())
        btn = st.form_submit_button("➕ Add Medicine", use_container_width=True)

    if btn:
        if not nm or cat == 'Select...':
            st.error("❌ Please fill all fields.")
        else:
            fresh = load()
            if (fresh['Medicine'].str.lower() == nm.lower()).any():
                st.error(f"❌ **{nm}** already exists. Go to Update Medicine tab.")
            else:
                new_row = pd.DataFrame([{'Medicine':nm,'Category':cat,'Current_Stock':stk,
                                         'Minimum_Stock':mn,'Unit_Price':prc,'Expiry_Date':pd.Timestamp(exp)}])
                fresh = pd.concat([fresh, new_row], ignore_index=True)
                save(fresh)
                st.success(f"✅ {nm} added successfully!")
                st.rerun()

# ── UPDATE EXISTING MEDICINE ──────────────────────────────────────────────────
with tab4:
    st.markdown("#### ✏️ Update Medicine")

    med = st.selectbox(
        "🔍 Search & Select Medicine",
        options=sorted(df['Medicine'].unique())
    )

    row = df[df['Medicine'] == med].iloc[0]

    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        if st.button("➖", key="minus"):
            if row['Current_Stock'] > 0:
                df.loc[df['Medicine']==med, 'Current_Stock'] -= 1
                save(df)
                st.rerun()

    with col2:
        st.markdown(
            f"<h3 style='text-align:center'>{row['Current_Stock']}</h3>",
            unsafe_allow_html=True
        )

    with col3:
        if st.button("➕", key="plus"):
            df.loc[df['Medicine']==med, 'Current_Stock'] += 1
            save(df)
            st.rerun()

    new_stock = st.number_input("Or Enter Exact Stock", value=int(row['Current_Stock']))

    if st.button("Update Exact Value"):
        df.loc[df['Medicine']==med, 'Current_Stock'] = new_stock
        save(df)
        st.success("Updated successfully")
        st.rerun()
# ── UPLOAD CSV ────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("#### 📁 Bulk Upload via CSV")
    st.info("Upload a CSV with these columns: `Medicine`, `Category`, `Current_Stock`, `Minimum_Stock`, `Unit_Price`, `Expiry_Date` (format: YYYY-MM-DD)")

    up = st.file_uploader("Choose CSV file", type=['csv'])
    if up:
        try:
            udf  = pd.read_csv(up)
            need = {'Medicine','Category','Current_Stock','Minimum_Stock','Unit_Price','Expiry_Date'}
            miss = need - set(udf.columns)
            if miss:
                st.error(f"❌ Missing columns: {', '.join(miss)}")
            else:
                st.success(f"✅ {len(udf)} records found")
                st.dataframe(udf.head(), use_container_width=True)
                if st.button("✅ Load into Inventory", type="primary", use_container_width=True):
                    udf.to_csv(FILE, index=False)
                    st.success("✅ Inventory updated!")
                    st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    st.markdown("---")
    sample = pd.DataFrame({
        'Medicine'     : ['Paracetamol','Insulin'],
        'Category'     : ['Painkiller','Diabetes'],
        'Current_Stock': [150,25],
        'Minimum_Stock': [50,20],
        'Unit_Price'   : [2,150],
        'Expiry_Date'  : ['2026-06-15','2026-05-20']
    })
    st.download_button("📥 Download Sample Template", sample.to_csv(index=False), "sample.csv", "text/csv")

st.markdown("---")
st.markdown("<p style='text-align:center;color:gray;font-size:12px'>MediTrack Pro • Because Every Medicine Counts.</p>",
            unsafe_allow_html=True)
