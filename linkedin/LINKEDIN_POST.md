**Does an AI agent really remember—or are we just sending more chat history?**

I built a Snowflake e-commerce support lighthouse to explore five different memory patterns using **one shared Cortex Agent**:

🔹 **M1 Stateless:** Answer the current order question without previous context.
🔹 **M2 Conversation:** Understand “Who is delivering it?” from earlier turns in the same session.
🔹 **M3 Episodic:** Recall an approved, customer-reported delivery complaint across conversations.
🔹 **M4 Semantic:** Remember the customer's current notification preference—EMAIL → SMS, with versioning and revocation.
🔹 **M5 Procedural:** Retrieve an approved delayed-order playbook, while independent SQL checks escalation eligibility.

**The architecture matters:** Streamlit + Python manage memory selection, retrieval, and context assembly. Snowflake stores governed memory and operational data. Cortex Agent uses Cortex Analyst and a semantic view for grounded investigation.

**Takeaway:** Enterprise agent memory isn't one giant conversation transcript. Historical events, current facts, and approved procedures need different lifecycles and controls.

These are **application-managed memory patterns built on Snowflake**, not five native Snowflake memory services. The demo uses synthetic data and does not claim production identity isolation.

Architecture below 👇

Code and walkthrough: [INSERT VERIFIED PUBLIC GITHUB URL]

#Snowflake #CortexAI #AgenticAI #DataArchitecture #AIGovernance
