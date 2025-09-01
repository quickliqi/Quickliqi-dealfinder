# QuickLiqi Deployment Guide

This repository contains the source code for the QuickLiqi application. The steps below describe how to deploy it on a fresh Ubuntu 22.04 server with Docker, configure DNS for a public domain, and verify the deployment.

## 1. VPS Preparation (Ubuntu 22.04)

### Install Docker and Docker Compose
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
sudo apt install -y docker-compose-plugin
```

### Clone the Repository and Configure the Environment
```bash
git clone https://github.com/QuickLiqi/Quickliqi-dealfinder.git
cd Quickliqi-dealfinder
cp .env.example .env  # or create the file manually
nano .env             # set Postgres, domain, and other secrets
```

### Start the Stack
```bash
docker compose up -d
```

## 2. DNS Configuration

Create an **A record** with your DNS provider that points your domain to the public IP of the VPS.

Example values:

| Host | Type | Value      |
|------|------|------------|
| @    | A    | `<VPS_IP>` |

Propagation can be checked from the server:
```bash
dig +short yourdomain.com
```
When the command returns your VPS IP, the record has propagated (this can take several minutes up to 24 hours).

## 3. Post-deployment Verification

1. **Backend health check**
   ```bash
   curl -f https://yourdomain.com/api/health
   ```
   A JSON response such as `{"status":"ok"}` confirms that the FastAPI backend is running.

2. **Frontend**
   Open `https://yourdomain.com` in a browser. The React build should load and display the application UI.

---

## Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

### Available Scripts

In the project directory, you can run:

#### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

#### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

#### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

#### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

### Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

#### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

#### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

#### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

#### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

#### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

#### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
