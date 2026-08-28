import streamlit as st
from google import genai
import json

# Streamlit UI Configuration
st.set_page_config(page_title="AI Trade Risk & Sentiment Checker", page_icon="📈", layout="centered")

st.title("📈 AI Trade Risk & Sentiment Checker")
st.caption("Telegram/News ke hype par trade lene se pehle apna Risk-to-Reward aur Logic verify karein.")

# API Key Streamlit Secrets se aayegi (user ko enter nahi karni)
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("⚠️ API Key configured nahi hai. App owner ko Streamlit Secrets set karne hain.")
    st.stop()

# Input Form
with st.form("trade_form"):
    st.subheader("1. Trade Details")
    col1, col2 = st.columns(2)
    with col1:
        asset_name = st.text_input("Asset / Stock Name", value="NIFTY / RELIANCE")
        trade_type = st.selectbox("Trade Type", ["BUY / LONG", "SELL / SHORT"])
        entry_price = st.number_input("Entry Price (₹)", min_value=0.0, value=1000.0, step=0.5)

    with col2:
        stop_loss = st.number_input("Stop Loss (₹)", min_value=0.0, value=980.0, step=0.5)
        target_price = st.number_input("Target Price (₹)", min_value=0.0, value=1050.0, step=0.5)

    st.subheader("2. Context & Reason")
    context_text = st.text_area(
        "Trade lene ka karan kya hai? (News, Telegram signal, Chart pattern, etc.)",
        placeholder="E.g., Telegram channel ne bola Breakout hai + Positive Quarterly Results aaye hain..."
    )

    submit_btn = st.form_submit_button("Analyze Trade Risk  🚀")

# Calculation Logic
if submit_btn:
    if entry_price <= 0 or stop_loss <= 0 or target_price <= 0:
        st.error("Sabhi prices valid aur 0 se bade hone chahiye.")
    elif not context_text.strip():
        st.error("Kripya trade lene ka context/reason likhein.")
    else:
        # Calculate Math Metrics (deterministic - AI ke bharose nahi)
        if trade_type == "BUY / LONG":
            risk = entry_price - stop_loss
            reward = target_price - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - target_price

        if risk <= 0:
            st.error("Invalid Stoploss! Long trade me Stoploss Entry price se kam, Short me zyada hona chahiye.")
        elif reward <= 0:
            st.error("Invalid Target! Target price wrong direction me hai.")
        else:
            rr_ratio = round(reward / risk, 2)

            prompt = f"""
You are a strict, unbiased Financial Risk Manager and Trading Psychology Assistant.
Analyze the following trade setup submitted by a retail trader. Do NOT give
investment advice or a buy/sell recommendation — only analyze sentiment and risk.

- Asset: {asset_name}
- Position Type: {trade_type}
- Entry Price: {entry_price}
- Stop Loss: {stop_loss} (Risk per unit: {risk})
- Target Price: {target_price} (Reward per unit: {reward})
- Calculated Risk-to-Reward Ratio: 1:{rr_ratio}
- Trader's Reason/Context: "{context_text}"

Respond ONLY in this strict JSON format, no markdown, no extra text:
{{
  "sentiment_score": <0-100 integer>,
  "sentiment_label": "<Fear-driven / Neutral / FOMO-driven>",
  "red_flags": ["flag1", "flag2"],
  "summary": "<one line plain-language summary in Hinglish>",
  "disclaimer": "Yeh educational analysis hai, investment advice nahi."
}}
"""

            try:
                with st.spinner("AI trade setup analyze kar raha hai..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )

                    raw_text = response.text.strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("```")[1]
                        if raw_text.startswith("json"):
                            raw_text = raw_text[4:]
                    raw_text = raw_text.strip()

                    result = json.loads(raw_text)

                st.subheader("📊 Analysis Result")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Risk-to-Reward Ratio", f"1 : {rr_ratio}")
                with col_b:
                    st.metric("Sentiment Score", f"{result['sentiment_score']}/100",
                               help=result.get("sentiment_label", ""))

                st.info(f"**Sentiment:** {result.get('sentiment_label', 'N/A')}")

                if result.get("red_flags"):
                    st.warning("**⚠️ Red Flags:**\n" + "\n".join(
                        f"- {flag}" for flag in result["red_flags"]))
                else:
                    st.success("No major red flags detected.")

                st.write(f"**Summary:** {result.get('summary', '')}")
                st.caption(result.get("disclaimer", "Yeh educational analysis hai, investment advice nahi."))

            except json.JSONDecodeError:
                st.error("AI ka response valid JSON nahi tha. Dobara try karein.")
            except Exception as e:
                st.error(f"Kuch error aaya: {str(e)}")
