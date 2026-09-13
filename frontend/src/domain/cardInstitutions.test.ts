import {describe,expect,it} from 'vitest'
import {CARD_INSTITUTIONS,cardInstitution,contrastRatio} from './cardInstitutions'

const approved=['nubank','itau','bradesco','santander','bb','caixa','inter','c6','btg','xp','picpay','mercado_pago','neon','sicoob','sicredi','other']

describe('CARD-CATALOG-01 accessible visual catalog',()=>{
 it('keeps all sixteen approved keys in stable order, including Neon and fallback',()=>{
  expect(CARD_INSTITUTIONS.map(item=>item.key)).toEqual(approved)
  expect(cardInstitution('neon').label).toBe('Neon')
  expect(cardInstitution('missing').key).toBe('other')
  expect(cardInstitution(undefined).label).toBe('Outra instituição')
 })

 it.each(CARD_INSTITUTIONS)('$label has AA text and visible control contrast',institution=>{
  expect(contrastRatio(institution.theme.text,institution.theme.background)).toBeGreaterThanOrEqual(4.5)
  expect(contrastRatio(institution.theme.text,institution.theme.surface)).toBeGreaterThanOrEqual(4.5)
  expect(contrastRatio(institution.theme.mutedText,institution.theme.background)).toBeGreaterThanOrEqual(4.5)
  expect(contrastRatio(institution.theme.accent,institution.theme.background)).toBeGreaterThanOrEqual(3)
  expect(contrastRatio(institution.theme.focusRing,institution.theme.background)).toBeGreaterThanOrEqual(3)
 })

 it('contains only local color tokens and text aliases, never remote logos or hotlinks',()=>{
  expect(JSON.stringify(CARD_INSTITUTIONS)).not.toMatch(/https?:|url\(|logo/i)
  expect(CARD_INSTITUTIONS.every(item=>Object.values(item.theme).every(value=>/^#[0-9a-f]{6}$/i.test(value)))).toBe(true)
 })
})
