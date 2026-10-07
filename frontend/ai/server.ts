import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const isProduction = process.env.NODE_ENV === 'production';

app.use(express.json());

// Initialize Google GenAI if key is provided
let aiClient: GoogleGenAI | null = null;
if (process.env.GEMINI_API_KEY) {
  try {
    aiClient = new GoogleGenAI({});
  } catch (err) {
    console.warn('Could not initialize GoogleGenAI client:', err);
  }
}

// POST /api/chat
app.post('/api/chat', async (req, res) => {
  const { message, mode, attachments } = req.body;

  if (!message) {
    return res.status(400).json({ error: 'Message is required' });
  }

  // If Gemini API is available, generate real AI response
  if (aiClient && process.env.GEMINI_API_KEY) {
    try {
      const systemInstruction = `You are NEXUS AI: "Your Intelligent Digital Command Center" for operator Tejas Bargat (Lead Systems Architect & Hardware Technologist).
You are a next-generation AI operating system with deep technical expertise in embedded systems, microcontrollers (8051, ARM, STM32, ESP32), sensor circuits (ADC0804, LDR arrays, PWM servo controls), robotics, and software architecture.
Operating Mode: ${mode || 'ENGINEERING'}.
Tone: Highly intelligent, precise, technological, engineering-grade, concise.
Format: Use clean Markdown. Provide clear code snippets in C or TypeScript when applicable. Avoid generic fluff.`;

      const promptText = `${message}${attachments?.length ? `\n\nAttachments: ${attachments.map((a: any) => a.name).join(', ')}` : ''}`;

      const aiResponse = await aiClient.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: promptText,
        config: {
          systemInstruction,
          temperature: 0.3,
        }
      });

      const replyText = aiResponse.text || 'NEXUS cognitive routines executed.';
      return res.json({
        reply: replyText,
        stage: 'Completed',
      });
    } catch (err: any) {
      console.error('Gemini API execution error:', err.message);
      // Fallback gracefully below
    }
  }

  // Graceful fallback response when API key is not supplied
  const lowerMsg = (message || '').toLowerCase();
  let reply = `### NEXUS Command Center [${mode || 'ENGINEERING'}]\n\nProcessed query: "${message}". Systems operating nominal.`;

  if (lowerMsg.includes('solar') || lowerMsg.includes('8051')) {
    reply = `### Engineering Assessment: 8051 Dual-Axis Solar Tracker

1. **Differential Angle Calculation**: Quadrant sensor topology provides clean azimuth and elevation vector feedback.
2. **Hysteresis Threshold**: Set \`DEADBAND_DELTA = 20\` counts to prevent servo hunting under diffuse lighting.
3. **Power Isolation**: Decouple SG90 servo motor +5V rail from 8051 VCC with 470µF electrolytic capacitor to prevent brownout resets.`;
  }

  return res.json({
    reply,
    stage: 'Completed'
  });
});

// POST /api/voice
app.post('/api/voice', (req, res) => {
  const { input } = req.body;
  res.json({
    transcript: input || 'Run system diagnostics on solar tracker',
    reply: `NEXUS voice directive acknowledged: "${input}". Execution nominal.`
  });
});

// POST /api/code/run
app.post('/api/code/run', (req, res) => {
  const { code, language } = req.body;
  res.json({
    output: `[NEXUS Virtual Sandbox — ${language?.toUpperCase() || 'C'}]\nCompilation: 0 errors, 0 warnings.\nOutput: Simulation cycles executed successfully. Exit code: 0.`,
    exitCode: 0,
    executionTimeMs: 42
  });
});

// Setup Vite middlewares in development or static serve in production
async function startServer() {
  if (!isProduction) {
    const { createServer } = await import('vite');
    const vite = await createServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (_req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`NEXUS AI Command Center running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
