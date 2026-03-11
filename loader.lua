local Exploit = identifyexecutor()
local players = game:GetService("Players")
local lp = players.LocalPlayer

if Exploit == "Codex" then
lp:Kick("Solaris | Use Delta for mobile")
end
if Exploit == "Solara" then
lp:Kick("Solaris | Use Velocity for Windows")
end
if Exploit == "Xeno" then
lp:Kick("Solaris | Use Velocity for Windows")
end
if game.GameId ~= 3150475059 then
lp:Kick("Solaris | Execute the script in Football Fusion 2!")
end

loadstring(game:HttpGet("https://cdn.snc.dev/69a3119532794750001823ca/ibi1k7h6w1e"))()
