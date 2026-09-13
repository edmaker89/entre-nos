import type {ReactNode} from 'react'

export function CardsGrid({children}:{children?:ReactNode}){
 return <div aria-label="Cartões cadastrados" className="cards-grid" style={{gridTemplateColumns:'repeat(auto-fill, minmax(min(100%, 280px), 340px))',maxInlineSize:'100%'}}>{children}</div>
}
