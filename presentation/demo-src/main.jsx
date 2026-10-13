import "./mock-api.js";
import "../../app/globals.css";
import { createRoot } from "react-dom/client";
import Home from "../../app/page.tsx";

createRoot(document.getElementById("root")).render(<Home />);
