from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from .models import CustomUser, RankResult, Billing
from django.contrib.auth import get_user_model
import random
import requests
import json



def landing_page(request):
    return render(request, 'core/landing.html')

# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         User = get_user_model()

#         try:
#             user_obj = User.objects.get(username=username)
#         except User.DoesNotExist:
#             user_obj = None

#         if user_obj and user_obj.check_password(password):
#             login(request, user_obj)

#             # Jika admin langsung dashboard
#             if user_obj.role == 'admin' or user_obj.is_superuser:
#                 return redirect('dashboard')
            
#             return redirect('pembayaran')
        
#             # # USER → cek Billing
#             # from .models import Billing
#             # billing = Billing.objects.filter(user=user_obj).first()

#             # if not billing:
#             #     # Belum ada data billing, wajib bayar
#             #     return redirect('pembayaran')

#             # if billing.status_pembayaran:
#             #     # Sudah bayar
#             #     if user_obj.is_active:
#             #         return redirect('dashboard')
#             #     else:
#             #         return render(request, 'core/tidak_aktif.html')
#             # else:
#             #     # Sudah upload bukti tapi belum dikonfirmasi admin
#             #     return render(request, 'core/pembayaran_diproses.html')

#         else:
#             messages.error(request, 'Username atau password salah.')

#     return render(request, 'core/login.html')
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            # Login dulu tanpa cek is_active (izinkan login user inactive)
            login(request, user)

            if user.role == 'admin' or user.is_superuser:
                return redirect('dashboard')

            # USER → cek Billing
            from .models import Billing
            billing = Billing.objects.filter(user=user).first()

            if not billing:
                # 1️⃣ Belum ada di Billing → wajib ke pembayaran
                return redirect('pembayaran')

            if billing.status_pembayaran:
                # 4️⃣ Sudah bayar
                if user.is_active:
                    return redirect('dashboard')  # 4️⃣ Sudah bayar + aktif → dashboard
                else:
                    return render(request, 'core/tidak_aktif.html')  # 3️⃣ Sudah bayar + belum aktif
            else:
                # 2️⃣ Ada Billing tapi belum bayar (status_pembayaran False)
                return render(request, 'core/pembayaran_diproses.html')

        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'core/login.html')

def generate_otp():
    return str(random.randint(100000, 999999))

def register_view(request):    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        password = request.POST.get('password')

        otp = generate_otp()

        # Simpan data sementara di session
        request.session['pending_user'] = {
            'username': username,
            'email': email,
            'whatsapp': whatsapp,
            'password': password,
            'otp': otp
        }

        # Kirim OTP ke WhatsApp
        send_whatsapp_direct(
            device_key='UMSZSzMyen40UdD',
            token='TMeTyUimv75LmlHRlCutowWU2z86QW',
            phone=whatsapp,
            message=f"Kode OTP Anda: {otp}"
        )

        messages.success(request, 'Kode OTP telah dikirim ke WhatsApp Anda.')
        return redirect('verify_otp')

    return render(request, 'core/register.html')

def verify_otp_view(request):
    pending_user = request.session.get('pending_user')

    if not pending_user:
        messages.error(request, "Tidak ada proses pendaftaran yang berlangsung.")
        return redirect('register')

    if request.method == 'POST':
        input_otp = request.POST.get('otp')
        if input_otp == pending_user['otp']:
            # Buat user baru
            user = CustomUser.objects.create_user(
                username=pending_user['username'],
                email=pending_user['email'],
                password=pending_user['password'],
                whatsapp_number=pending_user['whatsapp'],
                role='user',
                is_active=True
            )

            # Hapus data pending di session
            del request.session['pending_user']

            # Login user
            login(request, user)

            messages.success(request, 'OTP benar. Silakan lanjutkan ke pembayaran.')
            return redirect('pembayaran')

        else:
            messages.error(request, 'Kode OTP salah.')

    return render(request, 'core/verify_otp.html', {'user_obj': pending_user})


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.role == 'admin' or request.user.is_superuser:
        total_users = CustomUser.objects.count()
        total_pembayaran_sukses = Billing.objects.filter(status_pembayaran=True).count()
        total_rank = RankResult.objects.count()
        pending_billings = Billing.objects.filter(status_pembayaran=False).count()

        # Recent keyword checks (limit 5)
        recent_ranks = RankResult.objects.select_related('user').order_by('-checked_at')[:5]

        # Jika kamu tetap mau tampilkan users dan billing_users juga
        users = CustomUser.objects.all().order_by('-date_joined')
        billing_users = Billing.objects.select_related('user').order_by('status_pembayaran')

        return render(request, 'core/dashboard_admin.html', {
            'total_users': total_users,
            'total_pembayaran_sukses': total_pembayaran_sukses,
            'total_rank': total_rank,
            'pending_billings': pending_billings,
            'recent_ranks': recent_ranks,
            'users': users,
            'billing_users': billing_users
        })
    else:
        billing = Billing.objects.filter(user=request.user).first()
        if not billing or not billing.status_pembayaran or not request.user.is_active:
            messages.info(request, 'Pembayaran Anda sedang diproses admin. Silakan tunggu konfirmasi.')
            return render(request, 'core/pembayaran_sukses.html')

        history = RankResult.objects.filter(user=request.user).order_by('-checked_at')
        return render(request, 'core/dashboard_user.html', {
            'result': None,
            'history': history
        })
   
@login_required
def delete_user(request, user_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Kamu tidak punya akses.")
        return redirect('dashboard')

    user_obj = get_object_or_404(CustomUser, id=user_id)
    user_obj.delete()
    messages.success(request, "User berhasil dihapus.")
    
    # Redirect dengan indikator section users
    return redirect('/dashboard/?section=users')

@login_required
def update_user(request, user_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Kamu tidak punya akses.")
        return redirect('dashboard')

    user_obj = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        user_obj.username = request.POST.get('username')
        user_obj.email = request.POST.get('email')
        user_obj.whatsapp_number = request.POST.get('whatsapp')
        user_obj.role = request.POST.get('role')
        user_obj.save()

        messages.success(request, 'User berhasil diupdate.')
        return redirect('dashboard')

    return render(request, 'core/update_user.html', {'user_obj': user_obj})


@login_required
def approve_pembayaran(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
  
    billing = Billing.objects.filter(user=user).first()
    if billing:
        billing.status_pembayaran = True
        billing.save()

    # Update User
    user.is_active = True
    user.save()

    # Kirim WhatsApp konfirmasi aktif
    if user.whatsapp_number:
        send_whatsapp_direct(
            device_key='UMSZSzMyen40UdD',
            token='TMeTyUimv75LmlHRlCutowWU2z86QW',
            phone=user.whatsapp_number,
            message=f"Halo {user.username}, pembayaran Anda sudah diterima. Akun Anda sudah aktif. Silakan login."
        )

    messages.success(request, f"Pembayaran untuk {user.username} disetujui dan akun sudah aktif.")
    return redirect('dashboard')

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
    

def get_ranks_serpapi(keyword, domain, hl, gl, google_domain, num):
    api_key = "572db24d1b3554570e4013212f0b26160f44709c398abb0a65dee3428e1ed4e6"
    params = {
        "engine": "google",
        "q": keyword,
        "google_domain": google_domain,
        "hl": hl,
        "gl": gl,
        "num": num,
        "api_key": api_key
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    ranks = []
    if "organic_results" in data:
        for idx, result in enumerate(data["organic_results"]):
            link = result.get("link", "")
            if domain in link:
                ranks.append({
                    "position": idx + 1,
                    "link": link
                })
    return ranks

@login_required
def check_rank_view(request):
    result_data = None
    if request.method == "POST":
        domain = request.POST.get("domain")
        keyword = request.POST.get("keyword")
        hl = request.POST.get("hl")
        gl = request.POST.get("gl")
        google_domain = request.POST.get("google_domain")
        num = request.POST.get("num")

        # SerpAPI request
        api_key = "572db24d1b3554570e4013212f0b26160f44709c398abb0a65dee3428e1ed4e6"
        params = {
            "engine": "google",
            "q": keyword,
            "google_domain": google_domain,
            "hl": hl,
            "gl": gl,
            "num": num,
            "api_key": api_key
        }
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        ranks = []
        if "organic_results" in data:
            for idx, result in enumerate(data["organic_results"]):
                link = result.get("link", "")
                if domain in link:
                    ranks.append({
                        "position": idx + 1,
                        "link": link
                    })
                    # Simpan ke database
                    RankResult.objects.create(
                        user=request.user,
                        domain=domain,
                        keyword=keyword,
                        rank=idx + 1,
                        url_result=link
                    )

        result_data = {
            "domain": domain,
            "keyword": keyword,
            "num": num,
            "total_found": len(ranks),
            "ranks": ranks
        }

    return render(request, 'core/dashboard_user.html', {"result": result_data})

@login_required
def history_view(request):
    results = RankResult.objects.filter(user=request.user).order_by('-checked_at')
    return render(request, 'core/history.html', {'results': results})

@login_required
def pembayaran(request):
    if request.method == 'POST':
        metode = request.POST.get('metode')
        bukti_file = request.FILES.get('bukti')

        if not metode or not bukti_file:
            messages.error(request, 'Metode dan bukti pembayaran wajib diisi.')
            return redirect('pembayaran')

        # Simpan file bukti pembayaran
        fs = FileSystemStorage()
        filename = fs.save(bukti_file.name, bukti_file)
        file_url = request.build_absolute_uri(fs.url(filename))

        # Masukkan ke tabel Billing
        from .models import Billing
        Billing.objects.create(
            user=request.user,
            bukti_pembayaran=filename,  # simpan path file
            status_pembayaran=False
        )

        # Kirim WA ke admin (opsional)
        send_whatsapp_direct(
            device_key="UMSZSzMyen40UdD",
            token="TMeTyUimv75LmlHRlCutowWU2z86QW",
            phone="6285941051469",
            message=(
                f"Bukti transfer diterima.\n"
                f"User: {request.user.username}\n"
                f"Metode: {metode}\n"
                f"Nominal: Rp 199.000\n"
                f"Lihat bukti: {file_url}"
            )
        )

        messages.success(request, 'Bukti pembayaran dikirim. Tunggu persetujuan admin.')
        return redirect('pembayaran_sukses')

    return render(request, 'core/pembayaran.html')

def pembayaran_sukses(request):
    return render(request, 'core/pembayaran_sukses.html')

def pembayaran_diproses(request):
    # Hanya user yang belum aktif yang boleh ke sini
    if request.user.is_active:
        return redirect('dashboard')
    
    return render(request, 'core/pembayaran_diproses.html')

@login_required
def dashboard_section(request, section):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return HttpResponseForbidden("Tidak punya akses")

    if section == 'stats':
        return render(request, 'core/dashboard_stats.html', {
            'total_users': CustomUser.objects.count(),
            'total_pembayaran_sukses': Billing.objects.filter(status_pembayaran=True).count(),
            'total_rank': RankResult.objects.count()
        })
    elif section == 'users':
        return render(request, 'core/dashboard_users.html', {
            'users': CustomUser.objects.all().order_by('-date_joined')
        })
    elif section == 'billing':
        return render(request, 'core/dashboard_billing.html', {
            'billing_users': Billing.objects.select_related('user').order_by('status_pembayaran')
        })
    else:
        return HttpResponseNotFound("Section tidak ditemukan")

@login_required
def update_user_status(request, user_id, action):
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Kamu tidak punya akses.')
        return redirect('dashboard')

    user = get_object_or_404(CustomUser, id=user_id)

    if action == 'activate':
        user.is_active = True
        messages.success(request, f"{user.username} telah diaktifkan.")
    elif action == 'deactivate':
        user.is_active = False
        messages.success(request, f"{user.username} telah dinonaktifkan.")
    else:
        messages.error(request, "Aksi tidak valid.")
        return redirect('dashboard')

    user.save()
    return redirect('dashboard')
