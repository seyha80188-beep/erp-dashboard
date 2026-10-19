# YEM SEYHA - ERP Dashboard

ប្រព័ន្ធ ERP Dashboard សម្រាប់គ្រប់គ្រង និងតាមដានហិរញ្ញវត្ថុ អាជីវកម្ម ចំណូល ចំណាយ និងប្រាក់ចំណេញ ភ្ជាប់ផ្ទាល់ជាមួយ Google Sheets។

## រចនាសម្ព័ន្ធគម្រោង (Project Structure)
- `index.html` : ផ្ទាំង UI គ្រប់គ្រង មាន Header, Sidebar 12 Modules និង Login Modal
- `style.css` : រចនាបថពណ៌ក្រហមជ្រៅ `#B91C1C` ស៊ីគ្នាលើ Desktop និងទូរស័ព្ទ
- `app.js` : Logic ដំណើរការ UI, ការផ្ទៀងផ្ទាត់សិទ្ធិ (Auth) និងការគណនាទិន្នន័យ
- `vercel.json` : ការកំណត់ Route សម្រាប់ Vercel Deployment
- `api/auth.js` : Serverless Function សម្រាប់ Login និងចេញ Session Token
- `api/data.js` : Serverless Function ការពារ Google Sheet ID មិនឱ្យ Browser ឃើញ

## ព័ត៌មានគណនីលំនាំដើម (Default Admin Credentials)
- **Username** : `admin`
- **Password** : `seyha2026`

## Environment Variables (សម្រាប់កំណត់ក្នុង Vercel)
- `ERP_USER` : `admin` (ឬឈ្មោះតាមចិត្ត)
- `ERP_PASS` : `seyha2026` (ឬពាក្យសម្ងាត់ថ្មី)
- `ERP_SECRET` : `seyha-secret-key-super-secure-2026`
- `GOOGLE_SHEET_ID` : `1Kg74MK_M1ofUbCzDBKh5B1HxDUqTM8rsTNvbWXJdnoE`
