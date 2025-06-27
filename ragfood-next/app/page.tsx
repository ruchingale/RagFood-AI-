"use client";
import { useState } from "react";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const askQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnswer("");
    const res = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    setAnswer(data.answer);
    setLoading(false);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#111",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "sans-serif",
      }}
    >
      <h1 style={{ fontSize: 32, marginBottom: 24 }}>Ask about Food</h1>
      <form
        onSubmit={askQuestion}
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 16,
          width: 350,
          maxWidth: "90vw",
        }}
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a food question..."
          style={{
            padding: 12,
            borderRadius: 8,
            border: "1px solid #333",
            fontSize: 16,
            background: "#222",
            color: "#fff",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: 12,
            borderRadius: 8,
            border: "none",
            background: "#4f46e5",
            color: "#fff",
            fontWeight: "bold",
            fontSize: 16,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>
      {answer && (
        <div
          style={{
            marginTop: 32,
            background: "#222",
            padding: 24,
            borderRadius: 12,
            maxWidth: 500,
            width: "90vw",
            fontSize: 18,
            boxShadow: "0 2px 16px #0004",
          }}
        >
          <strong>Answer:</strong>
          <div style={{ marginTop: 8 }}>{answer}</div>
        </div>
      )}
    </div>
  );
}
