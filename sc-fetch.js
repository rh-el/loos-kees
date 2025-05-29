import 'dotenv/config'

const auth = async () => {
    const clientId = process.env.SOUNDCLOUD_CLIENT_ID
    const codeChallenge = process.env.SOUNDCLOUD_CODE_CHALLENGE
    const response = await fetch(`https://secure.soundcloud.com/authorize?client_id=${clientId}&redirect_uri=/&response_type=code&code_challenge=${codeChallenge}&code_challenge_method=S256&state=${process.env.SOUNDCLOUD_STATE}`)
    // const data = await response.json()
    console.log(response)
}

auth()

const getToken = async () => {
    const response = await fetch("https://secure.soundcloud.com/oauth/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "application/json; charset=utf-8",
            "Authorization": "Basic " + btoa(`${process.env.SOUNDCLOUD_CLIENT_ID}:${process.env.SOUNDCLOUD_CLIENT_SECRET}`)
        },
        body: new URLSearchParams({
            grant_type: "client_credentials"
        })
    })
    const data = await response.json()
    return data
}

// TOKEN FORMAT
// {
//   access_token: '2-304151--CuMZW5DfzbXhfWyXWLcESWZ',
//   token_type: 'Bearer',
//   expires_in: 3599,
//   refresh_token: 'mVA5AqW4sZDjeyKlFnN0Rdrazgp8xooT',
//   scope: ''
// }

const userInfos = async () => {
    // const token = await getToken()
    // console.log(token)
    const response = await fetch("https://api.soundcloud.com/me", {
        method: "GET",
        headers: {
            "accept": "application/json; charset=utf-8",
            "Authorization": `Bearer 2-304151--CuMZW5DfzbXhfWyXWLcESWZ`,
        }
    })
    const data = await response.json()
    return data
}

const getUser = async (username) => {
    const response = await fetch(`https://api.soundcloud.com/users?q=${username}`, {
        headers: {
            "accept": "application/json; charset=utf-8",
            "Authorization": `Bearer 2-304151--CuMZW5DfzbXhfWyXWLcESWZ`,
        }
    });
    const data = await response.json();
    const urn = data[0].urn
    return urn
}

// getUser("parhelic_shell"); 

const getLikes = async () => {
    const response = await fetch("https://api.soundcloud.com/users/soundcloud%3Ausers%3A953953/likes/tracks?access=playable%2Cpreview&linked_partitioning=true", {
        headers: {
            "accept": "application/json; charset=utf-8",
            "Authorization": `Bearer 2-304151--CuMZW5DfzbXhfWyXWLcESWZ`,
        }
    })
    const data = await response.json()
    console.log(data)
}
// getLikes()
// getToken()
// userInfos()