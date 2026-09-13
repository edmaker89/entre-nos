import React from 'react'
import {cleanup,fireEvent,render,screen} from '@testing-library/react'
import {afterEach,describe,expect,it,vi} from 'vitest'
import {PaymentCard,type PaymentCardData} from './PaymentCard'
import {CardsGrid} from './CardsGrid'

const card:PaymentCardData={id:'card',name:'Dia a dia',institution_key:'neon',institution:'Neon',network:'visa',last_four:'0042',holder_id:'douglas',closing_day:25,due_day:5}
afterEach(cleanup)

describe('CARD-UX-01 proportional card and grid',()=>{
 it('renders nickname, institution, holder, final, network and cycle dates',()=>{render(<PaymentCard card={card} holderName="Douglas" onEdit={()=>{}} onSelect={()=>{}}/>);const visual=screen.getByRole('article',{name:'Cartão Dia a dia'});expect(visual.textContent).toContain('Neon');expect(visual.textContent).toContain('Douglas');expect(visual.textContent).toContain('•••• 0042');expect(visual.textContent).toContain('Visa');expect(visual.textContent).toContain('Fecha 25');expect(visual.textContent).toContain('Vence 5')})
 it('uses the exact ID-1 ratio and compact maximum width',()=>{render(<PaymentCard card={card} holderName="Douglas" onEdit={()=>{}} onSelect={()=>{}}/>);const visual=screen.getByRole('article');expect(visual.style.aspectRatio).toBe('85.6 / 53.98');expect(visual.style.inlineSize).toBe('min(100%, 340px)');expect(visual.style.maxInlineSize).toBe('100%')})
 it('applies the stable institution theme',()=>{render(<PaymentCard card={card} holderName="Douglas" onEdit={()=>{}} onSelect={()=>{}}/>);expect(screen.getByRole('article').style.background).toContain('rgb(0, 83, 107)');expect(screen.getByRole('article').style.color).toContain('rgb(255, 255, 255)')})
 it('uses a neutral fallback for an unknown migrated institution',()=>{render(<PaymentCard card={{...card,institution_key:'legacy',institution:'Banco legado'}} holderName="Douglas" onEdit={()=>{}} onSelect={()=>{}}/>);expect(screen.getByRole('article').style.background).toContain('rgb(55, 68, 63)');expect(screen.getByText('Banco legado')).toBeTruthy()})
 it('omits optional final and network without placeholders on a saved card',()=>{render(<PaymentCard card={{...card,last_four:null,network:null}} holderName="Douglas" onEdit={()=>{}} onSelect={()=>{}}/>);expect(screen.queryByText(/••••/)).toBeNull();expect(screen.queryByText('Visa')).toBeNull()})
 it('keeps edit and invoice actions accessible and separate',()=>{const edit=vi.fn(),select=vi.fn();render(<PaymentCard card={card} holderName="Douglas" onEdit={edit} onSelect={select}/>);fireEvent.click(screen.getByRole('button',{name:'Editar Dia a dia'}));fireEvent.click(screen.getByRole('button',{name:'Ver faturas de Dia a dia'}));expect(edit).toHaveBeenCalledWith(card);expect(select).toHaveBeenCalledWith(card)})
 it.each([1,4,12])('renders a compact grid with %s cards',count=>{const cards=Array.from({length:count},(_,index)=>({...card,id:`card-${index}`,name:`Cartão ${index}`}));render(<CardsGrid>{cards.map(item=><PaymentCard key={item.id} card={item} holderName="Douglas" onEdit={()=>{}} onSelect={()=>{}}/>)}</CardsGrid>);expect(screen.getAllByRole('article')).toHaveLength(count);const grid=screen.getByLabelText('Cartões cadastrados');expect(grid.style.gridTemplateColumns).toBe('repeat(auto-fill, minmax(min(100%, 280px), 340px))');expect(grid.style.maxInlineSize).toBe('100%')})
 it('allows an empty grid without adding fake cards',()=>{render(<CardsGrid/>);expect(screen.getByLabelText('Cartões cadastrados').children).toHaveLength(0)})
})
