export type Usuario = {
    id: number,
    username: string,
    email: string,
    first_name: string,
    last_name: string,
    papel: string,
    is_active: boolean,
    password?: string
}