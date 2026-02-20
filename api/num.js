export default async function handler(req, res) {
  try {
    const { num } = req.query;

    if (!num) {
      return res.status(400).json({
        success: false,
        message: "Please provide num parameter"
      });
    }

    const response = await fetch(
      `https://num-to-info.alphamovies.workers.dev/api/numinfo?key=support-kro-sb&num=${num}`
    );

    const result = await response.json();
    const details = result.details || {};

    return res.status(200).json({
      success: true,
      api_created_by: "SHAYAN EXPLORER",
      requested_number: num,
      "Aadhaar person name": details["aadhaar Owner name"] || null,
      "aadhaar id": details.aadhaar || null,
      Address: details.Address || null,
      fathername: details["sim number father name"] || null
    });

  } catch (error) {
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
