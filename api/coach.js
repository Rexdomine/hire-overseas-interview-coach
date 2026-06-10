module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }
  const brainUrl = process.env.HERMES_BRAIN_URL;
  const brainToken = process.env.HERMES_BRAIN_TOKEN;
  if (!brainUrl) {
    return res.status(500).json({ error: 'HERMES_BRAIN_URL is not configured on Vercel.' });
  }
  try {
    const upstream = await fetch(`${brainUrl.replace(/\/$/, '')}/coach`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Hermes-Brain-Token': brainToken || '' },
      body: JSON.stringify(req.body || {})
    });
    const text = await upstream.text();
    res.status(upstream.status);
    res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json');
    return res.send(text);
  } catch (error) {
    return res.status(502).json({ error: 'Could not reach VPS Hermes brain', detail: String(error && error.message || error) });
  }
};
