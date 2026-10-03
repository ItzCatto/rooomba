// ─────────────────────────────────────────────────────────────────────────────
//  ROBOT CUSTOMIZATION
//  Edit this file on GitHub and commit. The site updates within a few minutes;
//  then reload the page on the tablet. His personality is in prompt.txt.
//
//  This repo is public, so never put your ElevenLabs key or passcode here.
//  Those stay in server.py on your PC.
// ─────────────────────────────────────────────────────────────────────────────
window.ROBOT_SETTINGS = {

  // ── Brain (your PC) ──
  brainUrl: '',             // Your PC's address from "tailscale funnel", e.g. 'https://robot.tail1234.ts.net'
  aiModel: '',              // Ollama model to use, e.g. 'llama3.2'. Empty = the PC's default
  memory: 10,               // How many back-and-forths he remembers in a conversation

  // ── Look ──
  eyeColor: '#FF6B21',      // Orange from the robot's sensor ring
  background: '#EFF1EE',    // White from the robot's shell
  size: 0.9,                // How much of the screen the eyes fill (0.5 to 1)
  eyeWidth: 22,             // Eye width (default 22)
  eyeHeight: 26,            // Eye height (default 26)
  eyeRoundness: 1,          // 1 = fully round, 0 = square corners
  eyeSpacing: 20,           // Distance from the middle of the screen to each eye (default 20)

  // ── Attitude ──
  lidHeaviness: 0.5,        // How far his lids hang at rest: 0 = wide open, 0.7 = barely open
  browTilt: 4,              // Tilt of his right lid in degrees, like a raised eyebrow. 0 = level
  blinkEvery: [3.5, 7],     // Seconds between lazy blinks (picks a random time in this range)
  sideEyeEvery: [4, 9],     // Seconds between side-eye glances. [0, 0] turns them off

  // ── Motion ──
  speakingBounce: 2.6,      // How high his eyes bounce while talking. 0 = no bounce
  motionBlur: 40,           // Motion blur length in milliseconds. 0 turns it off

  // ── Voice ──
  voiceId: 'PjC87YIKtz6Y7JFMZ1hh',   // ElevenLabs voice ID (Brad - Australian)
  voiceModel: 'eleven_flash_v2_5',    // eleven_flash_v2_5 = fastest, eleven_multilingual_v2 = best quality
  listenLanguage: 'en-US',            // Language he listens for, e.g. 'en-AU' or 'en-GB'
  backupVoiceRate: 1.05,              // The tablet's own voice, only used if ElevenLabs fails
  backupVoicePitch: 0.85,

  // ── Preview ──
  demo: true,               // Plays a demo loop while brainUrl is empty
};
