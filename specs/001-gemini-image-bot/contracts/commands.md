# Bot Command Contracts: Gemini Image Bot

**Branch**: `001-gemini-image-bot` | **Date**: 2026-03-24

Each entry defines the inputs, outputs, and error conditions for a bot slash command.
"Inputs" are what the user sends alongside the command; "Outputs" are what the bot sends
back. All commands are silent in group chats unless a slash command is present.

---

## /interpret

**Purpose**: Ask Gemini to describe or answer a question about an image.

### Inputs

| Element      | Required | Description                                                         |
|--------------|----------|---------------------------------------------------------------------|
| Photo        | Conditional | Must be attached to this message OR present in the active session context |
| Text (caption) | Optional | A question or instruction about the image (e.g., "What breed is this dog?") |

**Valid combinations**:
- Photo + text: interpret the photo with the given question
- Photo only: provide a general description of the photo
- Text only (no photo): use the image from the current session context; answer the follow-up question
- Neither (no photo, no text): error — missing image

### Outputs

| Condition              | Response type | Content                                                  |
|------------------------|---------------|----------------------------------------------------------|
| Success (long op)      | Text          | "Analysing your image…" acknowledgement ≤3 seconds       |
| Success (result)       | Text          | Natural-language description or answer from Gemini        |
| No image in msg or ctx | Text (error)  | "I need an image to work with. Please attach a photo…"   |
| Image too large        | Text (error)  | "That image is too large. Please send a photo under 10 MB." |
| Non-image media        | Text (error)  | "I can only process images (photos). Please attach a JPEG or PNG." |
| Session expired (context used) | Text (info) | "Your previous conversation has expired due to inactivity. Please re-share the image." |
| Gemini API error       | Text (error)  | "There was an issue with the Gemini API. Please try again in a moment." |

---

## /generate

**Purpose**: Generate a new image from a text description using Imagen.

### Inputs

| Element | Required | Description                                              |
|---------|----------|----------------------------------------------------------|
| Text    | Yes      | Description of the image to generate (e.g., "a cartoon cat wearing a sunhat") |
| Photo   | Ignored  | Attachments are ignored for this command                 |

### Outputs

| Condition              | Response type | Content                                                  |
|------------------------|---------------|----------------------------------------------------------|
| Success (long op)      | Text          | "Generating your image…" acknowledgement ≤3 seconds      |
| Success (result)       | Photo         | Generated image as a Telegram photo message               |
| Missing text prompt    | Text (error)  | "Please describe the image you'd like me to generate. Example: /generate a sunset over the mountains" |
| Content policy violation | Text (error) | "I wasn't able to generate that image. Please try a different description." |
| Gemini API error       | Text (error)  | "There was an issue with the Gemini API. Please try again in a moment." |

**Note**: Uses `gemini-3.1-flash-image-preview` by default. Model name is configurable via the `GEMINI_MODEL` environment variable.

---

## /modify

**Purpose**: Edit an existing image based on a text instruction.

### Inputs

| Element         | Required | Description                                               |
|-----------------|----------|-----------------------------------------------------------|
| Photo           | Conditional | Must be attached to this message OR the command must be a reply to a message containing a photo |
| Text (caption)  | Yes      | Modification instruction (e.g., "make the background blue") |

**Valid combinations**:
- Reply to an existing photo message + text: modify the referenced photo
- New message with photo attachment + text: modify the attached photo
- No photo (no attachment, not a reply to photo) + text: error — missing image
- Photo + no text: error — missing instruction

### Outputs

| Condition                      | Response type | Content                                                  |
|--------------------------------|---------------|----------------------------------------------------------|
| Success (long op)              | Text          | "Modifying your image…" acknowledgement ≤3 seconds       |
| Success (result)               | Photo         | Modified image as a Telegram photo message                |
| No image (not attached, not reply) | Text (error) | "I need an image to modify. Please attach a photo or reply to one." |
| No instruction text            | Text (error)  | "Please describe what you'd like me to change. Example: /modify make the sky orange" |
| Image too large                | Text (error)  | "That image is too large. Please send a photo under 10 MB." |
| Non-image media                | Text (error)  | "I can only process images (photos). Please attach a JPEG or PNG." |
| Unsupported modification       | Text (error)  | "I wasn't able to apply that change. Please try a different instruction." |
| Gemini API error               | Text (error)  | "There was an issue with the Gemini API. Please try again in a moment." |

**Note**: Uses `gemini-3.1-flash-image-preview` by default (configurable via `GEMINI_MODEL`).
Image editing may be deferred if the model's editing capability is not stable at
implementation time (see spec.md Assumptions).

---

## /reset

**Purpose**: Clear the conversation context for the current chat.

### Inputs

| Element | Required | Description       |
|---------|----------|-------------------|
| (none)  | —        | No arguments used |

### Outputs

| Condition      | Response type | Content                                                  |
|----------------|---------------|----------------------------------------------------------|
| Session exists | Text          | "Conversation cleared. I've forgotten our previous images — start fresh anytime!" |
| No session     | Text          | "There's nothing to clear — no active conversation in this chat." |

---

## /help

**Purpose**: Display the list of available commands.

### Inputs

| Element | Required | Description       |
|---------|----------|-------------------|
| (none)  | —        | No arguments used |

### Outputs

| Condition | Response type | Content                                                    |
|-----------|---------------|------------------------------------------------------------|
| Always    | Text          | Formatted list of all commands with one-line descriptions  |

**Expected help text format**:
```
Here's what I can do:

/interpret [question] — Describe or answer questions about a photo
/generate <description> — Generate a new image from your description
/modify <instruction> — Edit an existing photo (attach it or reply to one)
/reset — Clear our conversation history
/help — Show this message
```

---

## /start

**Purpose**: Welcome message sent when a user first starts the bot (Telegram default).

### Inputs

| Element | Required | Description       |
|---------|----------|-------------------|
| (none)  | —        | No arguments used |

### Outputs

| Condition | Response type | Content                                                    |
|-----------|---------------|------------------------------------------------------------|
| Always    | Text          | Welcome message + same content as /help                   |

---

## Unrecognised Commands

Any slash command not in the above list:

| Condition | Response type | Content                                             |
|-----------|---------------|-----------------------------------------------------|
| Unknown `/command` | Text  | "I don't know that command." + same content as /help |

---

## Common Error Message Principles

- MUST NOT contain stack traces, exception class names, or internal identifiers.
- MUST be actionable: tell the user what to do next.
- MUST be concise: one or two sentences maximum.
- MUST use consistent phrasing across all commands for the same error type
  (e.g., "There was an issue with the Gemini API" is always the Gemini error message).
