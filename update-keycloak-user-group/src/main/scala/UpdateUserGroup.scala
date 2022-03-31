import com.typesafe.config.ConfigFactory
import org.keycloak.OAuth2Constants
import org.keycloak.admin.client.resource.{RealmResource, UsersResource}
import org.keycloak.admin.client.{Keycloak, KeycloakBuilder}
import org.keycloak.representations.idm.GroupRepresentation

import scala.annotation.tailrec
import scala.io.{Source, StdIn}
import scala.jdk.CollectionConverters._
import scala.language.postfixOps

object UpdateUserGroup extends App {

  private val configuration = ConfigFactory.load()
  private val authUrl: String = configuration.getString("keycloak.url")
  private val userAdminClient: String = configuration.getString("keycloak.user.admin.client")
  private val userAdminSecret: String = configuration.getString("keycloak.user.admin.secret")

  private def keyCloakAdminClient(): Keycloak = KeycloakBuilder.builder()
    .serverUrl(s"$authUrl/auth")
    .realm("tdr")
    .clientId(userAdminClient)
    .clientSecret(userAdminSecret)
    .grantType(OAuth2Constants.CLIENT_CREDENTIALS)
    .build()

  val realm = keyCloakAdminClient().realm("tdr")

  def addUsersToJudgmentGroup = {
    val emails = Source.fromResource("emails.txt").getLines.toList
    val usersResource = realm.users()
    emails.flatMap(email => {
      for {
        userResource <- usersResource.search(email).asScala.headOption
        parentGroup <- realm.groups().groups().asScala.find(_.getName == "user_type")
        transferringBodyGroup <- realm.groups().groups().asScala.find(_.getName == "transferring_body_user")
        subGroup <- parentGroup.getSubGroups.asScala.find(_.getName == "judgment_user")
        incorrectSubGroup <- transferringBodyGroup.getSubGroups.asScala.find(_.getName == "Ministry of Justice")
        correctSubGroup <- transferringBodyGroup.getSubGroups.asScala.find(_.getName == "HM Courts and Tribunal Service")
      } yield {
        usersResource.get(userResource.getId).leaveGroup(incorrectSubGroup.getId)
        usersResource.get(userResource.getId).joinGroup(correctSubGroup.getId)
        println(s"Added $email to HM Courts and Tribunal Service group")
      }
    })
  }
  addUsersToJudgmentGroup
}
