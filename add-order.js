// api/add-order.js - Vercel Serverless Function to relay orders to Google Apps Script Webhook
module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const webhook = process.env.GOOGLE_SHEET_WEBHOOK || 'https://script.google.com/macros/s/AKfycbzeBF3VpCX-y4WdzjJ2dHN-ZBfMQ5ShjLIDwmuA0bgqyAeMulB2PmIuVH4nUL938zai/exec';

  try {
    const payload = req.body;
    // Mark action as addOrder
    const bodyToSend = {
      action: 'addOrder',
      type: 'order',
      ...payload
    };

    const webhookRes = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(bodyToSend)
    });

    let resultText = '';
    try {
      resultText = await webhookRes.text();
    } catch (e) {}

    return res.status(200).json({ 
      success: true, 
      message: 'Synced Order to Google Sheet successfully',
      sheetResponse: resultText
    });
  } catch (err) {
    return res.status(500).json({ success: false, error: err.message });
  }
};
