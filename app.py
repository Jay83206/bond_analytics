import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="Bond Analytics Dashboard",
    page_icon="📈",
    layout="wide",
)

# ── Bond Math Functions ──────────────────────────────────────────────────────

def bond_pv(coupon_rate, maturity, principal, discount_rate, payment_frequency=12):
    coupon_payment = principal * (coupon_rate / payment_frequency)
    periodic_rate = discount_rate / payment_frequency
    total_periods = maturity * payment_frequency
    if periodic_rate != 0:
        pv_coupons = coupon_payment * ((1 - (1 + periodic_rate) ** -total_periods) / periodic_rate)
    else:
        pv_coupons = coupon_payment * total_periods
    pv_principal = principal / ((1 + periodic_rate) ** total_periods)
    return pv_coupons + pv_principal


def bond_convexity(face_value, coupon_rate, ytm, periods, frequency=1, delta_y=0.01):
    periodic_ytm    = ytm / frequency
    periodic_coupon = (coupon_rate / frequency) * face_value
    price = weighted_cf_sum = convexity_sum = 0.0

    for t in range(1, periods + 1):
        cash_flow = periodic_coupon if t < periods else periodic_coupon + face_value
        pv = cash_flow / (1 + periodic_ytm) ** t
        price           += pv
        weighted_cf_sum += t * pv
        convexity_sum   += pv * t * (t + 1)

    macaulay_duration = (weighted_cf_sum / price) / frequency
    modified_duration = macaulay_duration / (1 + periodic_ytm)
    convexity = (convexity_sum / (price * (1 + periodic_ytm) ** 2)) / (frequency ** 2)

    def price_change(dy):
        return (-modified_duration * dy + 0.5 * convexity * dy ** 2) * 100

    return {
        "bond_price"              : round(price, 4),
        "macaulay_duration"       : round(macaulay_duration, 4),
        "modified_duration"       : round(modified_duration, 4),
        "convexity"               : round(convexity, 4),
        "price_change_minus_200"  : round(price_change(-0.02), 4),
        "price_change_minus_100"  : round(price_change(-0.01), 4),
        "price_change_minus_50"   : round(price_change(-0.005), 4),
        "price_change_plus_50"    : round(price_change(+0.005), 4),
        "price_change_plus_100"   : round(price_change(+0.01), 4),
        "price_change_plus_200"   : round(price_change(+0.02), 4),
    }


# ── Sidebar Controls ─────────────────────────────────────────────────────────

st.sidebar.header("⚙️ Bond Parameters")

face_value = st.sidebar.number_input("Face Value ($)", value=1000, step=100, min_value=100)
maturity   = st.sidebar.slider("Maturity (years)", 1, 30, 10)
frequency  = st.sidebar.selectbox("Payment Frequency", options=[1, 2, 4, 12],
                                   format_func=lambda x: {1:"Annual",2:"Semi-Annual",4:"Quarterly",12:"Monthly"}[x])

st.sidebar.markdown("---")
st.sidebar.subheader("Coupon Rates (%)")
coupon_min = st.sidebar.slider("Min Coupon", 1, 20, 5)
coupon_max = st.sidebar.slider("Max Coupon", 1, 20, 9)
coupon_step = st.sidebar.selectbox("Step (bps)", [50, 100, 200], index=1)

st.sidebar.subheader("YTM Range (%)")
ytm_min = st.sidebar.slider("Min YTM", 1, 20, 5)
ytm_max = st.sidebar.slider("Max YTM", 1, 20, 9)
ytm_step = st.sidebar.selectbox("Step (bps) ", [50, 100, 200], index=1)

# Build rate arrays
import numpy as np
coupon_rates = [round(r / 100, 4) for r in np.arange(coupon_min, coupon_max + 0.001, coupon_step / 100)]
ytm_rates    = [round(r / 100, 4) for r in np.arange(ytm_min,    ytm_max    + 0.001, ytm_step    / 100)]

if len(coupon_rates) == 0 or len(ytm_rates) == 0:
    st.error("Adjust sliders so that max ≥ min.")
    st.stop()

# ── Build DataFrame ───────────────────────────────────────────────────────────

records = []
for c in coupon_rates:
    for y in ytm_rates:
        result = bond_convexity(face_value=face_value, coupon_rate=c, ytm=y,
                                periods=maturity * frequency, frequency=frequency)
        records.append({
            "Coupon Rate (%)":      round(c * 100, 2),
            "YTM (%)":             round(y * 100, 2),
            "Bond Price ($)":      result["bond_price"],
            "Macaulay Duration":   result["macaulay_duration"],
            "Modified Duration":   result["modified_duration"],
            "Convexity":           result["convexity"],
            "ΔP -200bps (%)":     result["price_change_minus_200"],
            "ΔP -100bps (%)":     result["price_change_minus_100"],
            "ΔP  -50bps (%)":     result["price_change_minus_50"],
            "ΔP  +50bps (%)":     result["price_change_plus_50"],
            "ΔP +100bps (%)":     result["price_change_plus_100"],
            "ΔP +200bps (%)":     result["price_change_plus_200"],
        })

df = pd.DataFrame(records)

# ── Page Header ───────────────────────────────────────────────────────────────

st.title("📈 Bond Analytics Dashboard")
st.markdown("**Price · Duration · Convexity · Yield Shock Scenarios** — adjust parameters in the sidebar.")

# ── KPI Strip ─────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
col1.metric("Bonds Analysed",    f"{len(df)}")
col2.metric("Avg Bond Price",    f"${df['Bond Price ($)'].mean():,.2f}")
col3.metric("Avg Mod. Duration", f"{df['Modified Duration'].mean():.2f} yrs")
col4.metric("Avg Convexity",     f"{df['Convexity'].mean():.2f}")

st.markdown("---")

# ── Tab Layout ────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", "💹 Price Analysis", "⏱ Duration", "🔄 Convexity", "📋 Data Table"
])

# Colour palette
COLORS      = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0',
               '#00BCD4', '#FF5722', '#607D8B', '#8BC34A', '#FFC107']
FILL_COLORS = [c.replace(")", ",0.12)").replace("rgb","rgba") if c.startswith("rgb")
               else c for c in COLORS]  # fallback — overridden below
FILLS = [
    "rgba(33,150,243,0.12)", "rgba(76,175,80,0.12)", "rgba(255,152,0,0.12)",
    "rgba(233,30,99,0.12)",  "rgba(156,39,176,0.12)", "rgba(0,188,212,0.12)",
    "rgba(255,87,34,0.12)",  "rgba(96,125,139,0.12)", "rgba(139,195,74,0.12)",
    "rgba(255,193,7,0.12)",
]

ytm_labels = [f"{y}%" for y in df["YTM (%)"].unique()]

shocks_neg = [
    ("ΔP -200bps (%)", "-200bps", "rgba(183,28,28,0.85)"),
    ("ΔP -100bps (%)", "-100bps", "rgba(244,67,54,0.85)"),
    ("ΔP  -50bps (%)", "-50bps",  "rgba(255,138,128,0.85)"),
]
shocks_pos = [
    ("ΔP  +50bps (%)", "+50bps",  "rgba(128,226,160,0.85)"),
    ("ΔP +100bps (%)", "+100bps", "rgba(76,175,80,0.85)"),
    ("ΔP +200bps (%)", "+200bps", "rgba(27,94,32,0.85)"),
]

# ── TAB 1: Full Dashboard ─────────────────────────────────────────────────────
with tab1:
    n_cols = len(coupon_rates)
    if n_cols > 8:
        st.warning("Too many coupon rates selected — showing up to 8 for readability.")
        coupon_rates_dash = coupon_rates[:8]
    else:
        coupon_rates_dash = coupon_rates

    fig = make_subplots(
        rows=5, cols=len(coupon_rates_dash),
        subplot_titles=[f"Coupon {round(c*100,1)}%" for c in coupon_rates_dash] * 5,
        row_titles=["Bond Price ($)", "Macaulay & Modified Duration",
                    "Convexity", "Negative Yield Shocks", "Positive Yield Shocks"],
        vertical_spacing=0.07,
        horizontal_spacing=0.06,
    )

    for col_i, coupon in enumerate(coupon_rates_dash, start=1):
        subset = df[df["Coupon Rate (%)"] == round(coupon * 100, 2)].reset_index(drop=True)
        color  = COLORS[(col_i - 1) % len(COLORS)]
        fill   = FILLS[(col_i - 1) % len(FILLS)]
        show   = col_i == 1

        # Row 1 – Price
        fig.add_trace(go.Bar(
            x=ytm_labels, y=subset["Bond Price ($)"],
            name=f"Coupon {round(coupon*100,1)}%",
            marker_color=color, opacity=0.85,
            text=subset["Bond Price ($)"].apply(lambda v: f"${v:,.0f}"),
            textposition="outside", textfont=dict(size=7),
            showlegend=show, legendgroup=f"c{col_i}",
            hovertemplate="YTM: %{x}<br>Price: $%{y:,.2f}<extra></extra>",
        ), row=1, col=col_i)
        fig.add_hline(y=face_value, line_dash="dash", line_color="red", line_width=1.2,
                      row=1, col=col_i,
                      annotation_text="Par" if col_i == 1 else "",
                      annotation_font_size=8)

        # Row 2 – Duration
        for trace_name, col_name, dash, sym in [
            ("Macaulay", "Macaulay Duration", "solid",  "circle"),
            ("Modified", "Modified Duration", "dot",    "square"),
        ]:
            fig.add_trace(go.Scatter(
                x=ytm_labels, y=subset[col_name],
                mode="lines+markers",
                name=trace_name, line=dict(color=color, width=2, dash=dash),
                marker=dict(size=6, symbol=sym, color="white", line=dict(color=color, width=2)),
                fill="tozeroy" if trace_name == "Macaulay" else None,
                fillcolor=fill if trace_name == "Macaulay" else None,
                showlegend=False, legendgroup=f"c{col_i}",
                hovertemplate=f"YTM: %{{x}}<br>{trace_name}: %{{y:.4f}} yrs<extra></extra>",
            ), row=2, col=col_i)

        # Row 3 – Convexity
        fig.add_trace(go.Scatter(
            x=ytm_labels, y=subset["Convexity"],
            mode="lines+markers+text",
            name="Convexity", line=dict(color=color, width=2, dash="dash"),
            marker=dict(size=7, symbol="diamond", color="white", line=dict(color=color, width=2)),
            fill="tozeroy", fillcolor=fill,
            text=subset["Convexity"].apply(lambda v: f"{v:.1f}"),
            textposition="top center", textfont=dict(size=7),
            showlegend=False, legendgroup=f"c{col_i}",
            hovertemplate="YTM: %{x}<br>Convexity: %{y:.4f}<extra></extra>",
        ), row=3, col=col_i)

        # Row 4 – Negative shocks
        for col_name, label, bar_color in shocks_neg:
            fig.add_trace(go.Bar(
                x=ytm_labels, y=subset[col_name], name=label,
                marker_color=bar_color,
                text=subset[col_name].apply(lambda v: f"{v:.1f}%"),
                textposition="outside", textfont=dict(size=6),
                showlegend=show, legendgroup=f"shock_{label}",
                hovertemplate=f"Shock: {label}<br>YTM: %{{x}}<br>ΔPrice: %{{y:.2f}}%<extra></extra>",
            ), row=4, col=col_i)
        fig.add_hline(y=0, line_color="black", line_width=0.8, row=4, col=col_i)

        # Row 5 – Positive shocks
        for col_name, label, bar_color in shocks_pos:
            fig.add_trace(go.Bar(
                x=ytm_labels, y=subset[col_name], name=label,
                marker_color=bar_color,
                text=subset[col_name].apply(lambda v: f"{v:.1f}%"),
                textposition="outside", textfont=dict(size=6),
                showlegend=show, legendgroup=f"shock_{label}",
                hovertemplate=f"Shock: {label}<br>YTM: %{{x}}<br>ΔPrice: %{{y:.2f}}%<extra></extra>",
            ), row=5, col=col_i)
        fig.add_hline(y=0, line_color="black", line_width=0.8, row=5, col=col_i)

    # Axes
    row_cfg = {1:("Price ($)","$",""), 2:("Duration (yrs)","",""),
               3:("Convexity","",""), 4:("ΔPrice (%)","","%"), 5:("ΔPrice (%)","","%")}
    for row, (ylabel, prefix, suffix) in row_cfg.items():
        for c in range(1, len(coupon_rates_dash) + 1):
            fig.update_yaxes(title_text=ylabel if c==1 else "", gridcolor="#f0f0f0",
                             zeroline=True, zerolinecolor="#aaa",
                             tickprefix=prefix, ticksuffix=suffix, row=row, col=c)
            fig.update_xaxes(title_text="YTM" if row==5 else "",
                             gridcolor="#f0f0f0", row=row, col=c)

    fig.update_layout(
        height=1400,
        template="plotly_white",
        barmode="group",
        legend=dict(orientation="v", x=1.01, y=1, font=dict(size=9),
                    bgcolor="rgba(255,255,255,0.9)", bordercolor="#ccc", borderwidth=1),
        margin=dict(l=90, r=160, t=100, b=60),
        title=dict(text="<b>Bond Analytics Dashboard</b>", x=0.5, font=dict(size=16)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── TAB 2: Price Analysis ─────────────────────────────────────────────────────
with tab2:
    st.subheader("Bond Price vs YTM")
    fig2 = go.Figure()
    for i, coupon in enumerate(coupon_rates):
        subset = df[df["Coupon Rate (%)"] == round(coupon*100, 2)]
        color  = COLORS[i % len(COLORS)]
        fig2.add_trace(go.Scatter(
            x=subset["YTM (%)"], y=subset["Bond Price ($)"],
            mode="lines+markers",
            name=f"Coupon {round(coupon*100,1)}%",
            line=dict(color=color, width=2.5),
            marker=dict(size=8),
            hovertemplate="Coupon: " + f"{round(coupon*100,1)}%<br>YTM: %{x}%<br>Price: $%{y:,.2f}<extra></extra>",
        ))
    fig2.add_hline(y=face_value, line_dash="dash", line_color="red",
                   annotation_text=f"Par (${face_value:,})", annotation_position="right")
    fig2.update_layout(
        xaxis_title="YTM (%)", yaxis_title="Bond Price ($)",
        template="plotly_white", height=500, hovermode="x unified",
        legend=dict(title="Coupon Rate"),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Price Heatmap")
    pivot = df.pivot(index="Coupon Rate (%)", columns="YTM (%)", values="Bond Price ($)")
    fig_hm = go.Figure(go.Heatmap(
        z=pivot.values, x=[f"{c}%" for c in pivot.columns],
        y=[f"{r}%" for r in pivot.index],
        colorscale="RdYlGn", text=pivot.values,
        texttemplate="$%{text:,.0f}", textfont=dict(size=10),
        hovertemplate="Coupon: %{y}<br>YTM: %{x}<br>Price: $%{z:,.2f}<extra></extra>",
        colorbar=dict(title="Price ($)"),
    ))
    fig_hm.update_layout(xaxis_title="YTM (%)", yaxis_title="Coupon Rate (%)",
                         template="plotly_white", height=400)
    st.plotly_chart(fig_hm, use_container_width=True)


# ── TAB 3: Duration ───────────────────────────────────────────────────────────
with tab3:
    st.subheader("Duration Analysis")
    col_a, col_b = st.columns(2)

    with col_a:
        fig3a = go.Figure()
        for i, coupon in enumerate(coupon_rates):
            subset = df[df["Coupon Rate (%)"] == round(coupon*100, 2)]
            color  = COLORS[i % len(COLORS)]
            fig3a.add_trace(go.Scatter(
                x=subset["YTM (%)"], y=subset["Macaulay Duration"],
                mode="lines+markers", name=f"{round(coupon*100,1)}%",
                line=dict(color=color, width=2), marker=dict(size=7),
            ))
        fig3a.update_layout(title="Macaulay Duration", xaxis_title="YTM (%)",
                            yaxis_title="Years", template="plotly_white", height=380)
        st.plotly_chart(fig3a, use_container_width=True)

    with col_b:
        fig3b = go.Figure()
        for i, coupon in enumerate(coupon_rates):
            subset = df[df["Coupon Rate (%)"] == round(coupon*100, 2)]
            color  = COLORS[i % len(COLORS)]
            fig3b.add_trace(go.Scatter(
                x=subset["YTM (%)"], y=subset["Modified Duration"],
                mode="lines+markers", name=f"{round(coupon*100,1)}%",
                line=dict(color=color, width=2, dash="dot"), marker=dict(size=7),
            ))
        fig3b.update_layout(title="Modified Duration", xaxis_title="YTM (%)",
                            yaxis_title="Years", template="plotly_white", height=380)
        st.plotly_chart(fig3b, use_container_width=True)

    st.subheader("Duration Heatmaps")
    c1, c2 = st.columns(2)
    for col_widget, metric, title in [
        (c1, "Macaulay Duration", "Macaulay Duration (yrs)"),
        (c2, "Modified Duration", "Modified Duration (yrs)"),
    ]:
        piv = df.pivot(index="Coupon Rate (%)", columns="YTM (%)", values=metric)
        hm  = go.Figure(go.Heatmap(
            z=piv.values, x=[f"{c}%" for c in piv.columns],
            y=[f"{r}%" for r in piv.index],
            colorscale="Blues_r",
            text=piv.values, texttemplate="%{text:.2f}",
            colorbar=dict(title="Years"),
        ))
        hm.update_layout(title=title, xaxis_title="YTM (%)",
                         yaxis_title="Coupon (%)", template="plotly_white", height=350)
        col_widget.plotly_chart(hm, use_container_width=True)


# ── TAB 4: Convexity ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("Convexity & Yield Shock Analysis")
    fig4 = go.Figure()
    for i, coupon in enumerate(coupon_rates):
        subset = df[df["Coupon Rate (%)"] == round(coupon*100, 2)]
        color  = COLORS[i % len(COLORS)]
        fig4.add_trace(go.Scatter(
            x=subset["YTM (%)"], y=subset["Convexity"],
            mode="lines+markers+text",
            name=f"Coupon {round(coupon*100,1)}%",
            line=dict(color=color, width=2.5),
            marker=dict(size=8),
            text=subset["Convexity"].apply(lambda v: f"{v:.1f}"),
            textposition="top center", textfont=dict(size=8),
        ))
    fig4.update_layout(xaxis_title="YTM (%)", yaxis_title="Convexity",
                       template="plotly_white", height=420,
                       legend=dict(title="Coupon Rate"))
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Price Change Sensitivity (All Shock Scenarios)")
    shock_cols = {
        "-200bps": "ΔP -200bps (%)", "-100bps": "ΔP -100bps (%)",
        "-50bps":  "ΔP  -50bps (%)", "+50bps":  "ΔP  +50bps (%)",
        "+100bps": "ΔP +100bps (%)", "+200bps": "ΔP +200bps (%)",
    }
    shock_colors = {
        "-200bps": "rgba(183,28,28,0.85)",  "-100bps": "rgba(244,67,54,0.85)",
        "-50bps":  "rgba(255,138,128,0.85)", "+50bps":  "rgba(128,226,160,0.85)",
        "+100bps": "rgba(76,175,80,0.85)",   "+200bps": "rgba(27,94,32,0.85)",
    }
    selected_coupon = st.selectbox(
        "Select Coupon Rate",
        options=[round(c*100, 1) for c in coupon_rates],
        format_func=lambda x: f"{x}%"
    )
    subset_s = df[df["Coupon Rate (%)"] == selected_coupon]
    fig5 = go.Figure()
    for label, col_name in shock_cols.items():
        fig5.add_trace(go.Bar(
            x=[f"{y}%" for y in subset_s["YTM (%)"]],
            y=subset_s[col_name],
            name=label, marker_color=shock_colors[label],
            hovertemplate=f"Shock: {label}<br>YTM: %{{x}}<br>ΔPrice: %{{y:.2f}}%<extra></extra>",
        ))
    fig5.add_hline(y=0, line_color="black", line_width=1)
    fig5.update_layout(
        barmode="group", xaxis_title="YTM (%)", yaxis_title="Estimated ΔPrice (%)",
        template="plotly_white", height=420,
        legend=dict(title="Shock"),
        title=f"Yield Shock Scenarios — Coupon {selected_coupon}%",
    )
    st.plotly_chart(fig5, use_container_width=True)


# ── TAB 5: Data Table ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("Full Analytics Table")
    st.dataframe(
        df.style.format({
            "Bond Price ($)":    "${:,.4f}",
            "Macaulay Duration": "{:.4f}",
            "Modified Duration": "{:.4f}",
            "Convexity":         "{:.4f}",
            **{c: "{:.4f}%" for c in df.columns if "ΔP" in c},
        }).background_gradient(subset=["Convexity"], cmap="Blues")
          .background_gradient(subset=["Bond Price ($)"], cmap="RdYlGn"),
        use_container_width=True, height=500,
    )

    # Convexity Pivot
    st.subheader("Convexity Pivot (Coupon × YTM)")
    pivot_conv = df.pivot(index="Coupon Rate (%)", columns="YTM (%)", values="Convexity")
    st.dataframe(pivot_conv.style.format("{:.4f}").background_gradient(cmap="Blues"),
                 use_container_width=True)

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "bond_analytics.csv", "text/csv")

st.caption("Built with Streamlit · Plotly · Pure Python bond math — no external pricing library required.")
