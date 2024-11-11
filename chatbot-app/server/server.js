require('dotenv').config();
const express = require("express");
const { OpenAI } = require("openai"); // Import OpenAI directly from the openai package
const cors = require("cors");

const app = express();
const port = 3000;

// Initialize the OpenAI instance
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY, // Ensure your API key is set correctly
  engine: "gpt-3.5-turbo", // specify the model
});

app.use(express.json());
app.use(cors());

app.post("/chat", async (req, res) => {
  const { message } = req.body;

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-3.5-turbo",  // specify model
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: message },
      ],
    });

    const reply = completion.choices[0].message.content;

    res.json({ reply });
  } catch (error) {
    console.error("Error in chat:", error);
    res.status(500).send("Error generating response");
  }
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});