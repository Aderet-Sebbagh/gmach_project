const express = require('express');
const cors = require('cors');
require('dotenv').config();

const { prisma } = require('./db/prismaClient');

const app = express();
app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ ok: true, service: 'gmach api' });
});

// --- Items API ---
// GET /items -> list all items
app.get('/items', async (req, res) => {
  try {
    const items = await prisma.item.findMany({
      orderBy: { createdAt: 'desc' },
    });
    res.json(items);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch items' });
  }
});

// POST /items -> create item
app.post('/items', async (req, res) => {
  try {
    const { name, category, description, quantity, imageUrl, notes } = req.body;

    // minimal validation
    if (!name || !category) {
      return res.status(400).json({ error: 'name and category are required' });
    }

    const item = await prisma.item.create({
      data: {
        name,
        category,
        description: description ?? null,
        quantity: typeof quantity === 'number' ? quantity : 1,
        imageUrl: imageUrl ?? null,
        notes: notes ?? null,
      },
    });

    res.status(201).json(item);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create item' });
  }
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`API running on http://localhost:${port}`);
});
