# ✅ CHECKLIST SEBELUM DEPLOY

Pastikan semua ini sudah OK sebelum deploy ke cloud:

## 📦 FILE & DEPENDENCY

- [✅] File model ada: `rf_total_coliform_log1p_improved.joblib`
- [ ] File model size > 0 bytes (cek ukuran file)
- [✅] File `model_features_order.txt` ada
- [✅] File `backend_fastapi.py` ada
- [✅] File `inference_rf.py` ada
- [✅] File `requirements.txt` ada dan lengkap
- [✅] File `Procfile` ada
- [✅] File `runtime.txt` ada
- [✅] File `.gitignore` ada

## 🧪 TESTING LOCAL

- [ ] Backend bisa jalan: `uvicorn backend_fastapi:app --reload`
- [ ] Frontend bisa jalan: `npm run dev`
- [ ] API `/health` return `{"status":"ok"}`
- [ ] API `/predict` bisa predict dengan benar
- [ ] Tidak ada error di console
- [ ] Model load successfully tanpa warning

## 🔑 AKUN & TOOLS

- [ ] Punya akun GitHub (github.com)
- [ ] Punya akun Render (render.com) - bisa sign up dengan GitHub
- [ ] Git installed di komputer
- [ ] Tahu cara push ke GitHub

## 📁 REPOSITORY GITHUB

- [ ] Repository sudah dibuat di GitHub
- [ ] Semua file sudah di-push ke GitHub
- [ ] File `.joblib` ikut ter-upload (check di GitHub website)
- [ ] Repository visibility: Public (atau Private tapi akun pro)

## 🔧 CONFIGURATION

- [ ] CORS sudah di-setup di backend (allow_origins=["*"])
- [ ] Model path menggunakan environment variable
- [ ] Port menggunakan `$PORT` dari environment

## 📝 DOKUMENTASI

- [ ] README.md ada dan jelas
- [ ] DEPLOYMENT guide ada
- [ ] Contact info / help tersedia

---

## 🚀 SIAP DEPLOY!

Jika semua checklist di atas ✅, Anda siap deploy!

Lanjut ke: `DEPLOY_MUDAH.md`

---

## ❓ JIKA ADA YANG BELUM ✅

### File model tidak ada atau 0 bytes
```bash
# Re-train model atau copy dari backup
```

### Git belum installed
Download: https://git-scm.com/downloads

### Belum punya akun GitHub
Sign up: https://github.com/join

### Testing local gagal
```bash
# Reinstall dependencies
pip install -r requirements.txt
npm install
```

### File tidak bisa di-push karena terlalu besar
Model file > 100MB? Gunakan Git LFS:
```bash
git lfs install
git lfs track "*.joblib"
git add .gitattributes
git add rf_total_coliform_log1p_improved.joblib
git commit -m "Add model with LFS"
git push
```
