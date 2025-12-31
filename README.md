# Introduction 
TODO: Give a short introduction of your project. Let this section explain the objectives or the motivation behind this project. 

# Getting Started
TODO: Guide users through getting your code up and running on their own system. In this section you can talk about:
1.	Installation process
2.	Software dependencies
3.	Latest releases
4.	API references

## Local testbed (recommended for local development) ✅
Follow these steps to run the project locally with **testbed** environment for all services:

1. Ensure Docker is running.
2. (If images are private) Authenticate to your ACR and pull images:
   ```bash
   az login
   az acr login --name yhaodevopsacr
   docker compose -f docker-compose.dev.yml pull
   ```
3. Start services (dev file uses the `testbed` images but sets the web to call local testbed APIs):
   ```bash
   # Start the dev environment (uses testbed images, web points to localhost:8080/8082)
   docker compose -f docker-compose.dev.yml up -d

   # Or stop and remove the containers
   docker compose -f docker-compose.dev.yml down
   ```
4. Local endpoints:
   - Web: http://localhost:3000
   - API (testbed): http://localhost:8080
   - API2 (testbed): http://localhost:8082

Notes:
- The repo now contains environment-specific compose files:
  - `docker-compose.dev.yml` — local dev environment (uses `testbed` images, `VITE_ENV=Testbed`, web configured to call `http://localhost` APIs).
  - `docker-compose.testbed.yml` — testbed compose (images tagged `testbed`).
  - `docker-compose.prod.yml` — prod compose (images tagged `prod`).

- Workflow recommendations:
  - Avoid committing machine-specific override files (e.g., `docker-compose.override.yml`) to the repo. Those are easy to misapply to CI or be accidentally included in PRs.
  - For one-off testing with the latest remote images, create a temporary override and pass it to `docker compose`:

    ```powershell
    # fetch latest tags (example) and write a temporary override
    $tag_api=(az acr repository show-tags --name yhaodevopsacr --repository repos-api --orderby time_desc --top 1 --output tsv).Trim()
    $tag_api2=(az acr repository show-tags --name yhaodevopsacr --repository repos-api2 --orderby time_desc --top 1 --output tsv).Trim()
    $tag_web=(az acr repository show-tags --name yhaodevopsacr --repository repos-web --orderby time_desc --top 1 --output tsv).Trim()

    @"
    version: '3.9'
    services:
      api-testbed:
        image: yhaodevopsacr.azurecr.io/repos-api:$tag_api
      api2-testbed:
        image: yhaodevopsacr.azurecr.io/repos-api2:$tag_api2
      web-testbed:
        image: yhaodevopsacr.azurecr.io/repos-web:$tag_web
    "@ | Out-File -FilePath docker-compose.local-override.yml -Encoding utf8

    docker compose -f docker-compose.testbed.yml -f docker-compose.local-override.yml pull
    docker compose -f docker-compose.testbed.yml -f docker-compose.local-override.yml up -d

    # When finished, delete the temporary file
    Remove-Item docker-compose.local-override.yml
    ```

  - If you prefer persistent local config, add it to `.gitignore` and use a named file like `docker-compose.local.yml` so it won't be committed by accident.

- If you'd rather build web locally for faster iteration, change `web` in `docker-compose.dev.yml` to use `build:` and mount sources (I can add that example if you want).


# Build and Test
TODO: Describe and show how to build your code and run the tests. 

# Contribute
TODO: Explain how other users and developers can contribute to make your code better. 

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:
- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)