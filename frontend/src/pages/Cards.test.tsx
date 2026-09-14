import React from 'react'
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react'
import {afterEach,describe,expect,it,vi} from 'vitest'
import {Cards} from './Cards'
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),api:vi.fn(),createOperation:vi.fn()}))
import {api,createOperation} from '../api/client'

const auth={user:{id:'u',name:'Douglas'},members:[{id:'u',name:'Douglas'}],family_id:'f'}
const card={id:'c',version:1,name:'Principal',institution_key:'neon',institution:'Neon',network:'visa',last_four:'0042',holder_id:'u',closing_day:25,due_day:5}
const cycle={id:'cy',version:2,month:'2026-10-01',closing_date:'2026-09-25',due_date:'2026-10-05',paid_at:null,confirmed:false}
afterEach(()=>{cleanup();vi.clearAllMocks()})
const load=(cycles:any[]=[])=>vi.mocked(api).mockImplementation(async path=>path==='/cards'?[card]:cycles)

describe('CARD-UX-01 integrated card page',()=>{
 it('shows structured card holder and configured cycle days',async()=>{load();render(<Cards auth={auth}/>);const visual=await screen.findByRole('article',{name:'Cartão Principal'});expect(visual.textContent).toContain('Douglas');expect(visual.textContent).toContain('Fecha 25');expect(visual.textContent).toContain('Vence 5');expect(visual.textContent).toContain('•••• 0042')})
 it('creates a catalogued card and refreshes the grid',async()=>{load();const operation=vi.fn().mockResolvedValue({});vi.mocked(createOperation).mockReturnValue(operation);render(<Cards auth={auth}/>);fireEvent.click(await screen.findByRole('button',{name:'Novo cartão'}));fireEvent.change(screen.getByLabelText('Nome do cartão'),{target:{value:'Novo'}});fireEvent.click(screen.getByRole('button',{name:'Neon'}));fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));await waitFor(()=>expect(operation).toHaveBeenCalledTimes(1));expect(createOperation).toHaveBeenCalledWith('/cards','POST',expect.objectContaining({name:'Novo',institution_key:'neon'}))})
 it('edits a card with its version and structured fields',async()=>{load();const operation=vi.fn().mockResolvedValue({});vi.mocked(createOperation).mockReturnValue(operation);render(<Cards auth={auth}/>);fireEvent.click(await screen.findByRole('button',{name:'Editar Principal'}));fireEvent.change(screen.getByLabelText('Final do cartão'),{target:{value:'9876'}});fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));await waitFor(()=>expect(createOperation).toHaveBeenCalledWith('/cards/c','PATCH',expect.objectContaining({version:1,last_four:'9876'})))})
 it('loads the selected card cycles and opens payment modal',async()=>{load([cycle]);render(<Cards auth={auth}/>);fireEvent.click(await screen.findByRole('button',{name:'Ver faturas de Principal'}));expect(await screen.findByText('outubro de 2026')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Pagar fatura'}));expect(screen.getByRole('dialog',{name:'Pagar fatura'})).toBeTruthy()})
 it('confirms an invoice cycle with its current version',async()=>{load([cycle]);const operation=vi.fn().mockResolvedValue({});vi.mocked(createOperation).mockReturnValue(operation);render(<Cards auth={auth}/>);fireEvent.click(await screen.findByRole('button',{name:'Ver faturas de Principal'}));fireEvent.click(await screen.findByRole('button',{name:'Conferir'}));await waitFor(()=>expect(createOperation).toHaveBeenCalledWith('/cycles/cy/confirm','POST',{version:2}))})
 it('keeps the card form open with values when save fails',async()=>{load();vi.mocked(createOperation).mockReturnValue(vi.fn().mockRejectedValue(new Error('Falha ao salvar.')));render(<Cards auth={auth}/>);fireEvent.click(await screen.findByRole('button',{name:'Novo cartão'}));fireEvent.change(screen.getByLabelText('Nome do cartão'),{target:{value:'Preservado'}});fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));expect((await screen.findByRole('alert')).textContent).toBe('Falha ao salvar.');expect((screen.getByLabelText('Nome do cartão') as HTMLInputElement).value).toBe('Preservado');expect(screen.getByRole('dialog',{name:'Novo cartão'})).toBeTruthy()})
})
