module.exports = {
  apps: [
    {
      name: "sts2-wiki",
      cwd: __dirname,
      script: process.platform === "win32" ? "cmd.exe" : "npm",
      args: process.platform === "win32" ? "/c npm run start" : "run start",
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
    },
  ],
};
