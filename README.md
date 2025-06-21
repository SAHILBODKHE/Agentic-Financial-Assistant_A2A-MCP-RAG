# Bankbot
Run LLAMA using :

ollama run llama3.2

python3 server.py --connection_type sse

uvicorn client1:app --port 4000
python3 drafter1.py --connection_type sse

Great — you've uploaded the full **CIBC Comprehensive Travel Insurance Plan PDF**, and you're looking to **test your RAG implementation** by asking questions from it.

Here are **sample questions** (categorized) you can use to test your RAG system:

---

## 🧠 General Plan Info

1. What is the maximum coverage for Travel Medical Insurance under the CIBC Comprehensive Plan?
2. Who underwrites the travel insurance policy offered by CIBC?
3. What number should I call in case of a medical emergency abroad?

---

## ⚠️ Eligibility & Exclusions

4. Who is eligible for the CIBC Comprehensive Travel Insurance Plan?
5. What are the pre-existing condition exclusions for someone under 60?
6. What conditions make someone over 60 ineligible for coverage?
7. What happens if I don’t notify the Operations Centre before hospital admission?

---

## 🏥 Medical Coverage

8. What medical services are covered under Emergency Medical Insurance?
9. Is air ambulance included in the coverage?
10. What dental treatments are covered in case of accident or emergency?
11. What is the limit for prescription drug reimbursements?

---

## ✈️ Trip Interruption / Cancellation

12. Under what circumstances can I cancel my trip and receive reimbursement?
13. What are the covered reasons for trip interruption?
14. What is the maximum reimbursement for trip cancellation before departure?
15. What costs are covered if I have to return home due to a medical emergency?

---

## 🧳 Baggage & Personal Effects

16. How much coverage do I have for lost or stolen baggage?
17. Is coverage provided for delayed baggage?
18. Are pets included under any coverage plans?

---

## 💀 Accidental Death & Dismemberment

19. What is the payout if I lose sight in one eye due to a travel accident?
20. Are injuries while climbing or motor racing covered under the AD\&D section?

---

## 🗂️ Claims & Operations

21. How do I make a claim under this policy?
22. Can I extend my insurance coverage while I’m already traveling?
23. What documents are required to file a claim?

---

## 🌍 Travel Warnings & Limitations

24. Will I be covered if I travel to a country under a Global Affairs Canada travel warning?
25. Are there any limits for coverage during a trip break (when returning home temporarily)?

---

You can now feed these questions to your RAG client (e.g., `client.py`) and verify if it answers them correctly based on the document context.

Would you like help automating these questions into a batch test script?
