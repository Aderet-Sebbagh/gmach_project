const express = require('express');
const cors = require('cors');
require('dotenv').config({ path: '../../.env' });

const app = express();

// middleware
app.use(cors());
app.use(express.json());

// route בסיסי לבדיקה
app.get('/health', (req, res) => {
  res.json({ ok: true, service: 'gmach api' });
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`API running on http://localhost:${port}`);
});
