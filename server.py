#!/usr/bin/env python3
import os
import sys
import json
import time
import urllib.request
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = 8080
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
SHEET_ID = '1Kg74MK_M1ofUbCzDBKh5B1HxDUqTM8rsTNvbWXJdnoE'
WEBHOOK_URL = 'https://script.google.com/macros/s/AKfycbwA02pwY7decXviLTk9BKb_eOY0y6ubh8S11Wfi4cc_hkXcK6Ram-p8WtVTNGSTGKwGJg/exec'

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ERPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} - {args[1]}\n")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_POST(self):
        url_path = urllib.parse.urlparse(self.path).path

        # 1. /api/auth
        if url_path == '/api/auth':
            token = f"local_token_{int(time.time())}"
            data = {
                "success": True,
                "token": token,
                "user": {
                    "username": "admin",
                    "role": "អ្នកគ្រប់គ្រងប្រព័ន្ធ"
                }
            }
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 2. /api/add-expense
        if url_path == '/api/add-expense':
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len) if content_len > 0 else b''

            # Proxy to Google Apps Script webhook
            try:
                req = urllib.request.Request(
                    WEBHOOK_URL,
                    data=post_body,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = resp.read()
            except Exception as e:
                sys.stderr.write(f"Webhook error: {e}\n")

            resp_json = json.dumps({
                "success": True,
                "message": "Synced to Google Sheet successfully"
            }, ensure_ascii=False).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(resp_json)))
            self.end_headers()
            self.wfile.write(resp_json)
            return

        # 3. /api/add-order & /api/submit-order (Dual sync: Google Form + Master Sheet A1)
        if url_path in ('/api/add-order', '/api/submit-order'):
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len) if content_len > 0 else b''
            
            order_data = {}
            try:
                order_data = json.loads(post_body.decode('utf-8'))
            except Exception as e:
                pass

            # A. Forward to Company's Google Form if requested
            if order_data.get('submitToGoogleForm', True):
                try:
                    form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSd_hP30dqB-F5gCV44AuxcftgmoDjo5zzkN-NSMiK-1rDEqPQ/formResponse'
                    date_val = str(order_data.get('date', ''))
                    seller_val = str(order_data.get('seller', 'យឹម សីហា'))
                    form_fields = {
                        'entry.1581364351': date_val,
                        'entry.2053044994': str(order_data.get('team', 'Bech_Nora')),
                        'entry.193760049': seller_val,
                        'entry.1608045144': seller_val,
                        'entry.1250998064': str(order_data.get('sellerPhone', '0968180188')),
                        'entry.615821671': str(order_data.get('priceUsd', '')),
                        'entry.485783433': str(order_data.get('receiverName', '')),
                        'entry.1618786820': str(order_data.get('receiverPhone', '')),
                        'entry.1844490282': str(order_data.get('address', '')),
                        'entry.77621526': str(order_data.get('delivery', 'VET(COD)')),
                        'entry.1529022117': str(order_data.get('note', ''))
                    }
                    if '-' in date_val:
                        parts = date_val.split('-')
                        if len(parts) == 3:
                            form_fields['entry.1581364351_year'] = str(int(parts[0]))
                            form_fields['entry.1581364351_month'] = str(int(parts[1]))
                            form_fields['entry.1581364351_day'] = str(int(parts[2]))

                    prods = order_data.get('productsMap', {})
                    if prods.get('Kidney Pro'): form_fields['entry.1166279805'] = str(prods['Kidney Pro'])
                    if prods.get('Pro D.O'): form_fields['entry.1229436075'] = str(prods['Pro D.O'])
                    if prods.get('Emmi'): form_fields['entry.1958386252'] = str(prods['Emmi'])
                    if prods.get('S.G Pro'): form_fields['entry.629009419'] = str(prods['S.G Pro'])
                    if prods.get('Yong Liang Plus'): form_fields['entry.404230430'] = str(prods['Yong Liang Plus'])
                    if prods.get('Yong Liang'): form_fields['entry.2028258738'] = str(prods['Yong Liang'])

                    encoded_form = urllib.parse.urlencode(form_fields).encode('utf-8')
                    form_req = urllib.request.Request(
                        form_url,
                        data=encoded_form,
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'User-Agent': 'Mozilla/5.0'
                        }
                    )
                    with urllib.request.urlopen(form_req, timeout=12) as fresp:
                        pass
                except Exception as e:
                    sys.stderr.write(f"Google Form proxy error: {e}\n")

            # B. Proxy to Google Apps Script webhook for Master Sheet A1
            try:
                req = urllib.request.Request(
                    WEBHOOK_URL,
                    data=post_body,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = resp.read()
            except Exception as e:
                sys.stderr.write(f"Webhook error: {e}\n")

            resp_json = json.dumps({
                "success": True,
                "message": "Order processed and synced successfully"
            }, ensure_ascii=False).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(resp_json)))
            self.end_headers()
            self.wfile.write(resp_json)
            return

        self.send_error(404, "Not Found")

    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path).path

        # 1. /api/data (Proxy Google Sheets CSVs)
        if url_path == '/api/data':
            A1_SHEET_ID = '1GI-wAYeSR4o3rYo5QcghXb4_zNpLgIGNDl8_83XnrKk'
            gids = {
                'expensesCsv': (SHEET_ID, '859033776'),
                'incomesCsv': (SHEET_ID, '1280452951'),
                'teamSalesCsv': (SHEET_ID, '944458554'),
                'boostPlanCsv': (SHEET_ID, '455285947'),
                'formResponses1Csv': (SHEET_ID, '301276705'),
                'masterA1Csv': (SHEET_ID, '1102512547'),
                'a1DataInputCsv': (A1_SHEET_ID, '613388513'),
                'a1MasterDashboardCsv': (A1_SHEET_ID, '2105527680')
            }

            data = {}
            for key, (sid, gid) in gids.items():
                csv_url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
                try:
                    req = urllib.request.Request(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data[key] = response.read().decode('utf-8', errors='replace')
                except Exception as e:
                    sys.stderr.write(f"Failed fetching {key} ({gid}): {e}\n")
                    data[key] = ""

            resp_json = json.dumps({
                "success": True,
                "data": data
            }, ensure_ascii=False).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(resp_json)))
            self.end_headers()
            self.wfile.write(resp_json)
            return

        # Default static file serving handled by SimpleHTTPRequestHandler
        super().do_GET()

if __name__ == '__main__':
    print(f"Starting Multi-Threaded ERP Server on 0.0.0.0:{PORT}...")
    server = ThreadingHTTPServer(('0.0.0.0', PORT), ERPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
