# TODO
## V2.0
- [ ] Add feedback mechanism to ttc_control
  - Currently, Orbitlink doesn't display whether the remote host receives the ttc messages. Adding a response mechanism which copies the received data back to Orbitlink with a timestamp, and having orbitlink append the timestamp to the copied data would accomplish this.
- [ ] Support multiple controls sending/receiving data and provide feedback to main site
  - Need to find a way to have UDP communicate exclusively with one host until the communication is finished and then receive the data from the other. Some sort of buffer.

## Bug Fixes
- [ ] Fix image_gen() race condition in imagery_control.py that sometimes doesn't generate images locally due to the socket not closing after the first image write
- [ ] Add compatibility for the iframe on the index.html for Firefox and Edge
- [ ] 