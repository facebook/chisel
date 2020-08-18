# Contributing to Chisel
We want to make contributing to this project as easy and transparent as
possible.

## Pull Requests
We actively welcome your pull requests.

1. Fork the repo and create your branch from `master`. 
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation. 
4. Ensure the test suite passes. 
5. Make sure your code lints. 
6. If you haven't already, complete the Contributor License Agreement ("CLA").

## Contributor License Agreement ("CLA")
In order to accept your pull request, we need you to submit a CLA. You only need
to do this once to work on any of Facebook's open source projects.

Complete your CLA here: <https://developers.facebook.com/opensource/cla>

## Issues  
We use GitHub issues to track public bugs. Please ensure your description is
clear and has sufficient instructions to be able to reproduce the issue.

Facebook has a [bounty program](https://www.facebook.com/whitehat/) for the safe
disclosure of security bugs. In those cases, please go through the process
outlined on that page and do not file a public issue.

## Updating Chisel in Brew (for maintainers)
Most users have Chisel installed via Homebrew. In order to update the version they'll receive when using `brew install` or `brew update`, we have to make some manual changes.

1. Create a new release in the GitHub web interface.
2. Download the `tar.gz` for that release and run `shasum -a 256 <path>`.
3. Copy the URL for the `.tar.gz` on the release page.

Run:
```
brew bump-formula-pr --strict chisel \
--url=<GitHub .tar.gz URL> \
--sha256=<output of shasum>
```

More docs on the process are available on the [Homebrew site](https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request).

Example PRs:
- [Bump to 2.0.1](https://github.com/Homebrew/homebrew-core/pull/59799)
- [Bump to 2.0.0](https://github.com/Homebrew/homebrew-core/pull/50571)

## License
By contributing to Chisel, you agree that your contributions will be licensed
under its MIT license.

