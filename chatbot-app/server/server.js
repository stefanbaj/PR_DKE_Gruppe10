//openai imports
require('dotenv').config();
const express = require("express");
const { OpenAI } = require("openai"); 
const cors = require("cors");

const app = express();
const port = 3000;

//config
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY, 
  engine: "gpt-3.5-turbo", 
});

app.use(express.json());
app.use(cors());

//get post message
app.post("/chat", async (req, res) => {
  const { message } = req.body;
  //generate openai response
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
//start server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});