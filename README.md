This is my prototype for reducing brightness of a video if it detect's that there are significant changes to the light (e.g flashbang from video game).

The purpose of this is to reduce uncomfortability of changing lights too fast and the end purpose of this is to help people with sensitivity of light to enjoy video without a worry or even if it can to enjoy video game too.

Currently, to detect if there's changing light too fast is by calculating 1 frame "light" mean and then normalize it and then doing the same to the next frame, after getting those 2 numbers, i calculate the difference to determine how much "light" that is being changed. I decided to make the the window that is being calculated is 3 seconds, so for 60 FPS video it will be 180 frame that is being calculated. After getting all the difference between frame i apply mean to it to get a number between 0-1 on how severe the "light" is being changed which become the parameters that can be changed to suit the needs, if the needs is to be more aggresive then lower the threshold if the needs is to be more passive then increase the threshold. Lastly, i apply sliding windows with 1 second as the sliding windows so roughly about 60 frame. After determining which window is problematic, then i simply dim the light. 

Problem : 
- Dealing with flashing light more robust than just dim the light (Major and hard problem, can use neural network but data will be a problem as we need an input video and output video).
- Detecting the problematic frames (Major and simple problem, can use neural network but need a lot of data to be accurate but the data should be easy to label as the input is just a video and the output is which frame is problematic).

So my next step will be to solve the problem above, which i will need some guidance on.