import bcfetch from 'bandcamp-fetch';

const getAlbumTracklist = async (albumUrl) => {
    const params = {albumUrl: albumUrl}
    const album = bcfetch.album
    const info = await album.getInfo(params)
    const filteredTracks = []
    info.tracks.forEach((track) => {
        filteredTracks.push({ title: track.name, artist: info.artist.name })
    })
    return filteredTracks
}

const fetchBandcampData = async (cookie) => {
    bcfetch.setCookie(cookie.toString())
    const fan = bcfetch.fan
    const wishlist = await fan.getWishlist()
    
    const promises = wishlist.items.map(async (element) => {
        const albumUrl = element["url"]
        return await getAlbumTracklist(albumUrl)
    })
    const filteredElements = (await Promise.all(promises)).flat()
    console.log(JSON.stringify(filteredElements))
}

if (process.argv.length > 2) {
    const cookie = process.argv[2];
    fetchBandcampData(cookie)
} else {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.question("enter your bandcamp cookie: ", async (cookie) => {
        await fetchBandcampData(cookie)
        rl.close()
    })
}
