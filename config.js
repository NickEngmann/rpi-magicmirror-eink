var config = {
  "magicmirror_port": 8080, // magic mirror port
  "display_width": 800, // eink display height in px
  "display_height": 480, // eink display width in px
  "wait_to_load": 18, // wait seconds to load the site and display all data
  "refresh_interval": "0 */5 * * * *", // update eink every 10 minutes
  // https://github.com/kelektiv/node-cron#cron-ranges
  "timezone": "America / New_York", // https://www.inmotionhosting.com/support/website/general-server-setup/tz-ref-table
  "invert_color": true
};

/*************** DO NOT EDIT THE LINE BELOW ***************/
if (typeof module !== "undefined") {module.exports = config;}
