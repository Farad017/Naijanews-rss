# Nairaland Custom RSS Feed

This project creates a custom RSS 2.0 feed from Nairaland's **New Topics** pages.

The RSS items contain the requested information:
- Topic title
- Topic URL

The GitHub Actions workflow regenerates `feed.xml` once every hour.

## Setup

1. Create a new GitHub repository. A public repository is the simplest choice for GitHub Pages.
2. Upload all files from this project, preserving the `.github/workflows/update-feed.yml` path.
3. Go to **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select the `main` branch and the `/ (root)` folder, then save.
6. Go to **Actions** and open **Update Nairaland RSS**.
7. Run the workflow manually once using **Run workflow**.
8. After GitHub Pages publishes the repository, your feed will be:

   `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/feed.xml`

Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub username and repository name.

## Important

GitHub Actions scheduled workflows can sometimes run later than the scheduled minute. The workflow is configured for once per hour, but the exact execution time is controlled by GitHub.

The scraper fetches the first three Nairaland New Topics pages and keeps up to 150 unique topics. This covers all Nairaland sections represented in the New Topics listing, rather than only one forum.

If Nairaland changes its HTML structure, the scraper may need a small adjustment.
