SHREE KARNI COMPUTER — PRINT BY QR
===================================

यह शुरुआती Flask पैकेज है:
- ग्राहक QR स्कैन करके मोबाइल से PDF/JPG/PNG अपलोड कर सकता है।
- UPI या Cash भुगतान विकल्प।
- Admin Dashboard में ऑर्डर, फाइल डाउनलोड, भुगतान स्थिति और ऑर्डर स्थिति।
- Windows PC से Print बटन (फाइल Windows के default print application को भेजता है)।

महत्वपूर्ण:
1) आपकी पुरानी पूरी वेबसाइट को templates/index.html में कॉपी करें।
   पुराने HTML/CSS/JS को हटाएँ या छोटा न करें। इस फोल्डर में setup_home.html
   केवल तब दिखेगा जब index.html मौजूद नहीं है।
2) कीमतें app.py के PRINT_TYPES में डेमो के लिए हैं। अपनी दुकान की वास्तविक
   कीमतें बदलें।
3) Default Admin PIN 1234 है। इस्तेमाल से पहले Windows CMD में सेट करें:
   set ADMIN_PIN=अपना_नया_PIN
   set SECRET_KEY=कोई_लंबी_रैंडम_सीक्रेट_स्ट्रिंग
   फिर उसी CMD विंडो से python app.py चलाएँ।
4) UPI ID app.py में 7891411425@ptyes है। QR/UPI भुगतान का ऑटो सत्यापन
   इस संस्करण में नहीं है; दुकान पर भुगतान की पुष्टि Admin को करनी होगी।
5) यह सिस्टम स्थानीय Wi-Fi/मोबाइल हॉटस्पॉट नेटवर्क पर चलता है। ग्राहक का मोबाइल
   और दुकान का PC एक ही hotspot से जुड़ा होना चाहिए। Windows Firewall पूछे तो
   Python को Private network पर Allow करें।
6) ऑटो प्रिंट Windows के default app/driver पर निर्भर है। पहले PDF/image को
   PC पर manually खोलकर Canon G3012 से टेस्ट करें। सही paper size, copies,
   colour/B&W और PVC settings प्रिंट डायलॉग में जाँचें।

INSTALL (Windows 11):
---------------------
1. इस ZIP को Extract करें।
2. उस फोल्डर में CMD खोलें।
3. चलाएँ:
   py -m venv .venv
   .venv\Scripts\activate
   py -m pip install -r requirements.txt
   py app.py
4. PC पर खोलें: http://127.0.0.1:5000
5. QR: http://127.0.0.1:5000/qr
6. Admin: http://127.0.0.1:5000/admin  (पहली बार PIN 1234)

Mobile:
---------
app.py चालू होने पर CMD में Mobile URL दिखेगा, जैसे http://192.168.x.x:5000/order
मोबाइल पर वही URL खोलें या PC के /qr पेज का QR स्कैन करें।

Security note:
यह local-network starter है, public internet पर सीधे expose न करें। Admin PIN,
SECRET_KEY, file limits, backups और secure hosting को production से पहले मजबूत करें।
