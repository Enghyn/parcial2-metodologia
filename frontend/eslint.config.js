import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config({ ignores: ["src/dist/**"] }, js.configs.recommended, ...tseslint.configs.recommended, {
  files: ["src/**/*.{ts,tsx}", "test/**/*.ts"],
  rules: { "@typescript-eslint/no-explicit-any": "error" },
});
