export type Person={id:string,name:string}
export type AuthUser=Person&{email?:string,version?:number}
export type Auth={user:AuthUser,members:Person[],family_id:string}
