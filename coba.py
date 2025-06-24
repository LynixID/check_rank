import requests
import json

def send_whatsapp_direct(device_key, token, phone, message, file_url=None):
    api_url = 'https://api.quods.id/api/direct-send'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'device_key': device_key,
        'phone': phone,
        'message': message
    }

    # Tambahkan file_url jika diberikan
    if file_url:
        payload['file_url'] = file_url

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        print("Status code:", response.status_code)
        print("Response text:", response.text)

        if response.status_code != 200:
            print("❌ Status code bukan 200.")
            return None

        result = response.json()
        print("Parsed JSON result:", result)

        if result.get('status') == 'success':
            print("✅ Pesan berhasil dikirim.")
        else:
            print(f"❌ Gagal: {result.get('message')}")
        return result

    except Exception as e:
        print(f"⚠ Error mengirim WA: {e}")
        return None
  
send_whatsapp_direct(
                device_key='UMSZSzMyen40UdD',  # Ganti dengan device key Quods
                token='TMeTyUimv75LmlHRlCutowWU2z86QW',  # Ganti token
                # phone=user.whatsapp_number,
                phone="6283845586939",
                message=f"Kode OTP Anda: 087658",
                file_url= "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
            )