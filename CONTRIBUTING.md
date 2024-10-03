### Steps to Contribute:
1. Fork the repository.

2. Create an issue for new features or bug fixes:

    - Go to the Issues section of the repository.
    - Create a new issue, providing a detailed description of the feature or bug.
    - Ask to be assigned to that issue by commenting on it.
    - Wait for confirmation or assignment of the issue before proceeding.
    - Sync your fork with the upstream repository to ensure you're working with the latest code:

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/REPOSITORY_NAME.git
git fetch upstream
git checkout main
git merge upstream/main
```
3. Create a new branch for your feature or fix:

```bash
git checkout -b feature-name
```
4. Make your changes and commit them:

```bash
git commit -m "Add some feature"
```
5. Push your branch to your fork:

```bash
git push origin feature-name
```
6. Create a Pull Request (PR):

- Go to your fork on GitHub.
- Click on the Compare & Pull Request button.
- In the PR description, reference the issue you're addressing using the format Closes #ISSUE_NUMBER.
- Ensure the maintainers review your PR and provide any necessary feedback.

