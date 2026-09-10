import {defineConfig} from '@playwright/test'
export default defineConfig({testDir:'./e2e',fullyParallel:false,workers:1,use:{channel:process.env.PW_CHANNEL||undefined,baseURL:'http://127.0.0.1:5173',trace:'retain-on-failure'},webServer:{command:'npm run dev -- --port 5173',url:'http://127.0.0.1:5173',reuseExistingServer:true}})
