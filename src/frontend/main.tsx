import React from "react";
import ReactDOM from "react-dom/client";
import { AppRouter } from "./app/router";
import "./index.css";

const rootElement = document.getElementById("root");

if (rootElement === null) {
  throw new Error("Falta el elemento #root");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>,
);
