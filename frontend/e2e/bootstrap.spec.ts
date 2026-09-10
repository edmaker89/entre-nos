import {test,expect} from '@playwright/test'
test('T21 web entry is reachable',async({page})=>{await page.goto('/');await expect(page).toHaveTitle(/Entre Nós/)})
