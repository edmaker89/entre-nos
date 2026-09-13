import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
const apiTarget=process.env.API_TARGET??'http://127.0.0.1:8000'
export default defineConfig({plugins:[react()],server:{proxy:{'/api':apiTarget,'/health':apiTarget}},test:{environment:'jsdom',include:['src/**/*.test.ts','src/**/*.test.tsx']}})
