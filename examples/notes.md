## Image analysis

- Custom demosaicing is hard to compete with existing demosiacing algorithms (tried normalizing blue + green, setting values to "0" below certain values (both can be performed in custom demosaic algos))
- Demosaicing algorithms allow a user to boost certain wavelengths while ignoring others (using the raw black points option)
- I found that setting red to 100 and green to 70 for IGV demosaic algo really made the dark regions pop
- Running more iterations on the capture sharpening option can really clear up an image (diminishing returns after 50 iterations)
- White point correction turned down to .1 can also lead to more clear images
- kidney bean is a region of space with low green levels coming through


### Thoughts:
- adding in multiple LEDs as backlights (red and blue) could result in over exposure and result in a lower quality image
- A single green LED will likely produce the best image as wavelengths will bleed into the red and blue spectrum
- Prioritizing our green pixels will produce a crisper image as we have the most pixels there
- The blue pixels are largely underutilized. That is not to say they don't produce some image quality. It was found that normalizing them results in large amounts of noise in the image
- Raw images are significantly bigger than existing jpeg, about 9x bigger
- We could make raw images smaller by cutting out surrounding black region donut, doing this could get the image down to ~6mb(double check this, I don't think i ended up squaring the radius), this would make the image about 2.5x bigger
- I think we should avoid coming up with custom demosaic algorithm, and instead opt for using existing ones
- raw-therapee has a cli
- There are python packages that exist that will demosaic for you
- demosaicing seems to be CPU intensive, and is likely best done as a post processing step once off of the raspberry-pi, and onto some better hardware
- Use aws, heorku, or house a service in the shop
- Possibility of coming up with cloud computing service that we charge for

