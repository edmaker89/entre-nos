export type CardTheme={background:string;surface:string;text:string;mutedText:string;accent:string;focusRing:string}
export type CardInstitution={key:string;label:string;aliases:string[];theme:CardTheme}

const theme=(background:string,surface:string,accent:string):CardTheme=>({
 background,surface,text:'#ffffff',mutedText:'#f2f2f2',accent,focusRing:'#ffffff',
})

export const CARD_INSTITUTIONS:CardInstitution[]=[
 {key:'nubank',label:'Nubank',aliases:['nu','roxinho'],theme:theme('#3b0a57','#4a0d69','#d9b4ea')},
 {key:'itau',label:'Itaú',aliases:['itau unibanco'],theme:theme('#703000','#592600','#ffd2ad')},
 {key:'bradesco',label:'Bradesco',aliases:[],theme:theme('#78002d','#600024','#ffb5cf')},
 {key:'santander',label:'Santander',aliases:[],theme:theme('#780b13','#60090f','#ffc1c5')},
 {key:'bb',label:'Banco do Brasil',aliases:['bb'],theme:theme('#153560','#102b4e','#ffe36e')},
 {key:'caixa',label:'Caixa',aliases:['caixa econômica'],theme:theme('#07506b','#064056','#7ce2ff')},
 {key:'inter',label:'Inter',aliases:['banco inter'],theme:theme('#793000','#612600','#ffd0a8')},
 {key:'c6',label:'C6 Bank',aliases:['c6'],theme:theme('#202124','#111214','#d7d9dc')},
 {key:'btg',label:'BTG Pactual',aliases:['btg'],theme:theme('#00375b','#002c49','#81d4ff')},
 {key:'xp',label:'XP',aliases:['xp investimentos'],theme:theme('#171717','#080808','#e5c96f')},
 {key:'picpay',label:'PicPay',aliases:[],theme:theme('#075e45','#064b38','#87e9c2')},
 {key:'mercado_pago',label:'Mercado Pago',aliases:['mercado pago'],theme:theme('#004b87','#003c6c','#8ed4ff')},
 {key:'neon',label:'Neon',aliases:['banco neon'],theme:theme('#00536b','#004256','#70e7ff')},
 {key:'sicoob',label:'Sicoob',aliases:[],theme:theme('#075246','#064138','#94e7d4')},
 {key:'sicredi',label:'Sicredi',aliases:[],theme:theme('#285014','#203f10','#bfe99f')},
 {key:'other',label:'Outra instituição',aliases:['outra'],theme:theme('#37443f','#2c3632','#b7d5c9')},
]

export const CARD_NETWORKS=[
 {key:'visa',label:'Visa'},{key:'mastercard',label:'Mastercard'},{key:'elo',label:'Elo'},
 {key:'amex',label:'American Express'},{key:'hipercard',label:'Hipercard'},{key:'other',label:'Outra'},
]

export function cardInstitution(key?:string){
 return CARD_INSTITUTIONS.find(item=>item.key===key)??CARD_INSTITUTIONS.at(-1)!
}

function luminance(color:string){
 const channels=color.slice(1).match(/.{2}/g)!.map(value=>parseInt(value,16)/255).map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4)
 return .2126*channels[0]+.7152*channels[1]+.0722*channels[2]
}

export function contrastRatio(first:string,second:string){
 const [light,dark]=[luminance(first),luminance(second)].sort((a,b)=>b-a)
 return (light+.05)/(dark+.05)
}
