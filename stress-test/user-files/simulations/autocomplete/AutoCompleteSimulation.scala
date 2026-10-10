import scala.concurrent.duration._

import io.gatling.core.Predef._
import io.gatling.http.Predef._


class AutoCompleteSimulation
  extends Simulation {

  val baseUrl = sys.env.getOrElse("BASE_URL", "http://localhost:8000")
  val peakUsersPerSec = sys.env.getOrElse("PEAK_USERS_PER_SEC", "20").toDouble
  val rampSeconds = sys.env.getOrElse("RAMP_SECONDS", "120").toInt

  // an user does not type the whole term: after some letters the term is already suggested
  val maxTypedLetters = 6
  val longestValidTerm = 48

  val httpProtocol = http
    .baseUrl(baseUrl)
    .userAgentHeader("Agente do Caos - Trie")

  val typeAndSelectTerm = scenario("Type And Maybe Select A Term")
    .feed(tsv("search-terms.tsv").circular())
    .exec(session => {
      val term = session("term").as[String]
      val prefixes = (1 to math.min(term.length, maxTypedLetters)).map(term.take(_))
      session.set("prefixes", prefixes)
    })
    // one request for each typed letter
    .foreach("#{prefixes}", "prefix") {
      exec(
        http("auto-complete")
        .get("/auto-complete")
        .queryParam("term", "#{prefix}")
        .queryParam("amount", "5")
        .check(status.is(200))
      )
      .pause(100.milliseconds, 300.milliseconds)
    }
    // not every user chooses a term after typing
    .randomSwitch(
      70.0 -> exec(
        http("select")
        .post("/auto-complete/select")
        .body(StringBody("""{"term": #{term.jsonStringify()}}"""))
        .header("content-type", "application/json")
        .check(status.is(204))
      )
    )

  val invalidAutoComplete = scenario("Invalid Auto Complete")
    .exec(
      http("invalid auto-complete")
      .get("/auto-complete")
      .queryParam("term", "a" * (longestValidTerm + 1))
      .queryParam("amount", "5")
      // 422 for a term longer than the limit
      .check(status.is(422))
    )

  setUp(
    typeAndSelectTerm.inject(
      constantUsersPerSec(1).during(10.seconds), // warm up

      rampUsersPerSec(1).to(peakUsersPerSec).during(rampSeconds.seconds)
    ),
    invalidAutoComplete.inject(
      constantUsersPerSec(1).during(10.seconds), // warm up

      rampUsersPerSec(1).to(peakUsersPerSec / 4).during(rampSeconds.seconds)
    )
  ).protocols(httpProtocol)
}
