# Adding New Project Templates

This document outlines the process for adding new project templates to the system, including instructions for both human developers and AI agents.

## Possible Next Template Ideas

Here are some suggestions for additional templates to consider adding:

*   **Vue.js (JavaScript/TypeScript):** A progressive JavaScript framework for building user interfaces.
*   **Angular (TypeScript):** A platform and framework for building single-page client applications using HTML and TypeScript.
*   **Go (Gin/Echo/Fiber):** For high-performance backend APIs in Go.
*   **Java (Spring Boot):** A widely used framework for building robust, production-ready Spring applications.
*   **React Native / Flutter:** For cross-platform mobile application development.

## Instructions for Adding a New Template

To add a new project template, follow these steps:

1.  **Create a new directory** under `src/mcp_tools/templates/` for your new template. The directory name should be descriptive and use `snake_case` (e.g., `vue_js`, `spring_boot`).
2.  **Populate the new template directory** with the necessary files and folders for your chosen technology. These files should represent a minimal, runnable project.
    *   Include a `README.md` file explaining how to get started with the template.
    *   Include a `.gitignore` file appropriate for the technology.
    *   Use placeholder names for project-specific elements (e.g., `ProjectName.csproj` for .NET, `project_name` for Python packages) that can be replaced during project creation.
3.  **Update `src/mcp_tools/project_templates.py`**:
    *   Add a new class variable to the `ProjectTemplates` class.
    *   The variable name should be in `UPPER_SNAKE_CASE` and correspond to your template (e.g., `VUE_JS`, `SPRING_BOOT`).
    *   The value should be a dictionary with `name`, `description`, and `files` keys.
    *   The `files` key should call `_load_template_files("your_template_directory_name")`.

    Example for a hypothetical Vue.js template:

    ```python
    # ... existing templates ...

    VUE_JS = {
        "name": "Vue.js Application",
        "description": "A basic Vue.js project with a single component.",
        "files": _load_template_files("vue_js")
    }
    ```
4.  **Review `src/mcp_tools/command_execution_tools.py`**:
    *   Check if any new commands or execution methods are needed for the new template (e.g., `dotnet` commands, `go build` commands).
    *   If so, add new functions or extend existing ones to safely execute these commands.
    *   Ensure any new commands are added to the `allowed_commands` lists within the respective `run_*_command` functions.

## AI Prompt Example for Adding a New Template

To instruct the AI to add a new template, you can use a prompt similar to this:

```
Please add a template for [Technology Name] (e.g., "Vue.js").

Here's a basic file structure and content for the template:

[Provide a detailed list of files and their content, or describe the structure and ask the AI to generate typical content. For example:]

- Directory: src/mcp_tools/templates/vue_js
- Files:
    - vue_js/package.json:
        ```json
        {
          "name": "vue-project",
          "version": "0.0.0",
          "private": true,
          "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
          },
          "dependencies": {
            "vue": "^3.3.4"
          },
          "devDependencies": {
            "@vitejs/plugin-vue": "^4.3.4",
            "vite": "^4.4.9"
          }
        }
        ```
    - vue_js/index.html:
        ```html
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8">
            <link rel="icon" href="/favicon.ico">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vite App</title>
          </head>
          <body>
            <div id="app"></div>
            <script type="module" src="/src/main.js"></script>
          </body>
        </html>
        ```
    - vue_js/src/main.js:
        ```javascript
        import { createApp } from 'vue'
        import App from './App.vue'
        import './assets/main.css'

        createApp(App).mount('#app')
        ```
    - vue_js/src/App.vue:
        ```vue
        <script setup>
        import HelloWorld from './components/HelloWorld.vue'
        </script>

        <template>
          <header>
            <img alt="Vue logo" class="logo" src="./assets/logo.svg" width="125" height="125" />

            <div class="wrapper">
              <HelloWorld msg="You did it!" />
            </div>
          </header>

          <main>
            <TheWelcome />
          </main>
        </template>

        <style scoped>
        /* ... styles ... */
        </style>
        ```
    - vue_js/src/components/HelloWorld.vue:
        ```vue
        <script setup>
        defineProps({
          msg: {
            type: String,
            required: true
          }
        })
        </script>

        <template>
          <div class="greetings">
            <h1 class="green">{{ msg }}</h1>
            <h3>
              You’ve successfully created a project with
              <a href="https://vitejs.dev/" target="_blank" rel="noopener">Vite</a> +
              <a href="https://vuejs.org/" target="_blank" rel="noopener">Vue 3</a>.
            </h3>
          </div>
        </template>

        <style scoped>
        /* ... styles ... */
        </style>
        ```
    - vue_js/.gitignore:
        ```
        node_modules
        dist
        .env
        .env.*
        npm-debug.log*
        yarn-debug.log*
        yarn-error.log*
        # ... other ignores ...
        ```
    - vue_js/README.md:
        ```markdown
        # Vue.js Project

        This is a basic Vue.js project created with Vite.

        ## Setup

        ```bash
        npm install
        ```

        ## Compiles and Hot-Reloads for Development

        ```bash
        npm run dev
        ```

        ## Compiles and Minifies for Production

        ```bash
        npm run build
        ```
        ```

Then, ensure you update `src/mcp_tools/project_templates.py` and `src/mcp_tools/command_execution_tools.py` as necessary.
