# Video Chat Transcript AI

An AI-powered chat application that provides intelligent, citable answers by leveraging a knowledge base built from video chat transcripts. This project utilizes a **RAG (Retrieval-Augmented Generation)** architecture to allow a Large Language Model (LLM) to perform deep Q&A on specific, unstructured conversation data, ensuring responses are accurate, context-aware, and verifiable.

![Demo Screenshot](https://i.imgur.com/example-screenshot.png)
*(tbd)*

---

## ✨ Features

* **🤖 Core RAG Architecture**: Implements a full Retrieval-Augmented Generation pipeline, effectively combining an LLM with a private knowledge base of chat transcripts. This solves the problem of knowledge gaps and "hallucinations" in general-purpose models.
* **⚙️ Automated Data Processing**: Includes scripts and methodologies for automated preprocessing of video chat transcript data, transforming raw conversation logs into structured, retrievable knowledge segments.
* **🔍 High-Precision Semantic Search**: Utilizes a vector database and semantic similarity search to efficiently and accurately retrieve the most relevant conversational snippets from the knowledge base in response to user queries.
* **📝 Advanced Prompt Engineering**: Features a sophisticated, persona-driven system prompt with strict output formatting instructions, guiding the LLM to generate responses that are stylistically consistent and include verifiable source citations (e.g., video links with timestamps).
* **🌐 Modern Web Application**: A full-stack application built with Next.js and React, providing a responsive and user-friendly chat interface for seamless interaction.
* **🚀 CI/CD & Global Deployment**: Deployed on Vercel with automated CI/CD pipelines, ensuring seamless updates and high-performance global access for users anywhere.

## 🛠️ Tech Stack

* **Frontend**: [Next.js](https://nextjs.org/), [React](https://react.dev/), [Tailwind CSS](https://tailwindcss.com/)
* **AI Backend & Workflow**: [Dify.ai](https://dify.ai/) (Cloud Version)
* **LLM (Large Language Model)**: [DeepSeek](https://www.deepseek.com/) (or your chosen model)
* **Deployment**: [Vercel](https://vercel.com/)
* **Node.js Version**: 20.x (LTS)

## 🚀 Getting Started

Follow these instructions to set up and run the project locally for development and testing.

### Prerequisites

* [Node.js](https://nodejs.org/) (Version 20.x recommended)
* [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/)
* A Dify.ai account and a configured application with an API key.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/brucezhao1875/video-chat-transcript-web.git](https://github.com/YourUsername/video-chat-transcript-web.git)
    cd video-chat-transcript-web
    ```
    
2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up environment variables:**
    Create a file named `.env.local` in the root of the project and add the following environment variables. You can get these from your Dify application's "API Access" section.

    ```env
    # Your Dify application's API endpoint
    NEXT_PUBLIC_API_URL=[https://api.dify.ai/v1](https://api.dify.ai/v1)
    
    # Your Dify application's API Key
    NEXT_PUBLIC_APP_API_KEY=app-xxxxxxxxxxxxxxxxxxxx
    ```

4.  **Run the development server:**
    ```bash
    npm run dev
    ```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the application running.

## 部署 (Deployment)

This project is optimized for deployment on [Vercel](https://vercel.com/).

1.  Push your code to a Git repository (e.g., on GitHub).
2.  Import the repository into Vercel.
3.  Configure the same environment variables (`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_APP_API_KEY`) in the Vercel project settings.
4.  Deploy! Vercel will automatically handle the build process and deployment for you.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
